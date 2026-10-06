"""Exportador do arquivo do Gate 1 (item D.2): `dataset/raw/compras_gov/<data>/` -> importação.

Gera, de forma determinística (duas execuções dão arquivos idênticos):
- `dataset/demo/inventario_demo.csv`: 100 linhas, 92 válidas e 8 inválidas de propósito, no
  formato de `POST /importacoes`, com a coluna extra `erro_proposital` nas 8 inválidas;
- `dataset/demo/fornecedores_demo.csv` (`razao_social`, `cnpj`): os fornecedores das linhas
  válidas, para o carregador `etl.carregar_fornecedores`;
- `dataset/demo/inventario_demo.LEIAME.md`: a metodologia e os números do que foi descartado.

Uso (a partir de `python/`): `python -m etl.exportar_inventario_demo`.

Regras (decisões da equipe, ver graphify-out/DIAGNOSTICO_D2.md e o LEIAME gerado):
só esfera federal; descarta identificador estrangeiro, CNPJ com mais de uma razão social, razão
social com mais de um CNPJ e itens com `(idCompra, idCompraItem)` repetido; por PDM, só preços
entre os percentis 10 e 90 dos registros federais; `numero_serie = CG-{idItemCompra}-001`, um
identificador técnico sintético (a fonte pública não traz número de série).
"""

import argparse
import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from etl.paths import DATASET_DIR

DATA_COLETA = "2026-10-05"
FONTE = "compras_gov"
# PDM do CATMAT -> categoria do seed (DIAGNOSTICO_D2.md, seção 4). A ordem é a do arquivo.
CATEGORIA_POR_PDM = {
    8435: "Notebook",
    6661: "Desktop",
    6484: "Desktop",
    10293: "Servidor",
    6669: "Monitor",
    5522: "Switch",
    237: "Roteador",
    15287: "Impressora",
    19246: "Tablet",
}
COLUNAS = [
    "nome",
    "tipo",
    "categoria",
    "fornecedor",
    "numero_serie",
    "chave_licenca",
    "data_aquisicao",
    "valor_compra",
    "localizacao",
    "data_source",
    "erro_proposital",
]
TOTAL_LINHAS = 100
TOTAL_VALIDAS = 92
LIMITE_NOME = 120
DATA_FUTURA = "2099-12-31"  # distante: o arquivo não deixa de ser inválido com o tempo
CENTAVO = Decimal("0.01")
# Razão social que é o nome de uma pessoa física (microempreendedor): "64.956.713 NOME DA PESSOA"
# (prefixo do CNPJ e o nome) ou o formato antigo, o nome seguido de 11 dígitos. Fora do arquivo.
PESSOA_FISICA_PREFIXO = re.compile(r"^\d{2}\.\d{3}\.\d{3}\s")
PESSOA_FISICA_ONZE_DIGITOS = re.compile(r"(?<!\d)\d{11}(?!\d)")

# numero_linha do relatório (cabeçalho = 1), campo, valor/erro inserido, motivo esperado.
# Um erro por linha: 8 linhas rejeitadas são 8 erros no relatório.
INVALIDAS = [
    (7, "nome", "nome com menos de 3 caracteres", "Nome deve ter ao menos 3 caracteres."),
    (18, "tipo", "tipo fora do domínio", "Tipo deve ser HARDWARE ou SOFTWARE."),
    (31, "categoria", "categoria inexistente", "Categoria não encontrada."),
    (46, "fornecedor", "fornecedor não cadastrado", "Fornecedor não encontrado."),
    (
        58,
        "numero_serie",
        "HARDWARE sem número de série",
        "Obrigatório para ativos do tipo HARDWARE (BR-002).",
    ),
    (
        71,
        "numero_serie",
        "número de série repetido no arquivo",
        "Duplicado dentro do próprio arquivo (AC-046).",
    ),
    (84, "data_aquisicao", "data futura", "Não pode ser futura (BR-003)."),
    (97, "valor_compra", "valor zero", "Deve ser maior que zero (BR-004)."),
]
LINHA_DA_SERIE_REPETIDA = 5  # a primeira ocorrência (válida) do número de série da linha 71


class ErroExportacao(Exception):
    """A coleta não permite montar o arquivo nas condições decididas."""


def ler_registros(pasta: Path) -> list[dict]:
    registros: list[dict] = []
    for arquivo in sorted(pasta.glob("*.json")):
        registros.extend(json.loads(arquivo.read_text(encoding="utf-8"))["resultado"])
    return registros


def _pdm(registro: dict) -> int:
    return int(registro["codigoPdm"])


def _razao(registro: dict) -> str:
    return registro["nomeFornecedor"].strip()


def arredondar(valor: float) -> Decimal:
    """2 casas, ROUND_HALF_UP, a partir da representação decimal mais curta do número."""
    return Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def percentis(valores: list[float]) -> tuple[float, float]:
    """P10 e P90 por interpolação linear (método inclusivo, o `linear` do numpy)."""
    if len(valores) == 1:  # `quantiles` pede 2 pontos; com 1, os dois percentis são o próprio valor
        return valores[0], valores[0]
    cortes = statistics.quantiles(valores, n=10, method="inclusive")
    return cortes[0], cortes[-1]


def nome_do_ativo(registro: dict) -> str:
    """`nomePdm + " " + marca`, sem espaços sobrando, no máximo 120 caracteres.

    Marca ausente (vazia ou só pontuação, como `-` e `.`): só o `nomePdm`."""
    marca = registro["marca"].strip()
    marca = marca if any(c.isalnum() for c in marca) else ""
    return " ".join(f"{registro['nomePdm']} {marca}".split())[:LIMITE_NOME].rstrip()


def razao_de_pessoa_fisica(razao: str) -> bool:
    return bool(PESSOA_FISICA_PREFIXO.match(razao) or PESSOA_FISICA_ONZE_DIGITOS.search(razao))


def cnpj_formatado(cnpj: str) -> str:
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def filtrar(registros: list[dict]) -> dict:
    """Aplica os filtros em ordem e devolve os elegíveis, as faixas e a contagem de cada passo.

    O que se repete (CNPJ com mais de uma razão social e vice-versa, `(idCompra, idCompraItem)`)
    é medido sobre todos os registros coletados; os percentis, só sobre os federais."""
    razoes_por_cnpj = defaultdict(set)
    cnpjs_por_razao = defaultdict(set)
    chaves = Counter((r["idCompra"], r["idCompraItem"]) for r in registros)
    for r in registros:
        razoes_por_cnpj[r["niFornecedor"]].add(_razao(r))
        cnpjs_por_razao[_razao(r)].add(r["niFornecedor"])

    federais = [r for r in registros if r["esfera"] == "F"]
    precos = defaultdict(list)
    for r in federais:
        precos[_pdm(r)].append(r["precoUnitario"])
    faixas = {pdm: percentis(valores) for pdm, valores in precos.items()}

    passos = [
        (
            "identificador de fornecedor estrangeiro",
            lambda r: len(r["niFornecedor"]) != 14 or not r["niFornecedor"].isdigit(),
        ),
        (
            "razão social de pessoa física (microempreendedor)",
            lambda r: razao_de_pessoa_fisica(_razao(r)),
        ),
        (
            "CNPJ com mais de uma razão social",
            lambda r: len(razoes_por_cnpj[r["niFornecedor"]]) > 1,
        ),
        ("razão social com mais de um CNPJ", lambda r: len(cnpjs_por_razao[_razao(r)]) > 1),
        (
            "item com (idCompra, idCompraItem) repetido",
            lambda r: chaves[(r["idCompra"], r["idCompraItem"])] > 1,
        ),
        (
            "preço fora da faixa P10-P90 do PDM",
            lambda r: not (faixas[_pdm(r)][0] <= r["precoUnitario"] <= faixas[_pdm(r)][1]),
        ),
    ]
    restantes = federais
    descartes = []
    for rotulo, descartar in passos:
        mantidos = [r for r in restantes if not descartar(r)]
        descartes.append((rotulo, len(restantes) - len(mantidos)))
        restantes = mantidos
    return {
        "coletados": len(registros),
        "federais": federais,
        "descartes": descartes,
        "elegiveis": restantes,
        "faixas": faixas,
    }


def _rodizio(pool: list[dict]) -> list[dict]:
    """Os registros do PDM 1 na ordem de `CATEGORIA_POR_PDM`, depois o 2º de cada PDM...: a
    cobertura dos PDMs vem antes do volume e a ordem é total (determinística)."""
    pares: list[tuple[int, int, dict]] = []
    for ordem, pdm in enumerate(CATEGORIA_POR_PDM):
        do_pdm = sorted((r for r in pool if _pdm(r) == pdm), key=lambda r: r["idItemCompra"])
        pares.extend((posicao, ordem, r) for posicao, r in enumerate(do_pdm))
    return [r for _, _, r in sorted(pares, key=lambda t: (t[0], t[1]))]


def _fornecedores_escolhidos(por_cnpj: dict[str, list[dict]], alvo: int) -> list[str]:
    """Menor conjunto, pela ordem de volume, que cobre os PDMs e junta `alvo` registros.

    Primeiro garante cada PDM com o fornecedor de maior volume que o atende; depois completa o
    volume pelo ranking (mais registros primeiro, CNPJ como desempate)."""
    ranking = sorted(por_cnpj, key=lambda c: (-len(por_cnpj[c]), c))
    pdms_de = {c: {_pdm(r) for r in por_cnpj[c]} for c in ranking}
    escolhidos: list[str] = []
    cobertos: set[int] = set()
    for pdm in CATEGORIA_POR_PDM:
        if pdm in cobertos:
            continue
        candidatos = [c for c in ranking if pdm in pdms_de[c]]
        if not candidatos:
            raise ErroExportacao(f"nenhum registro elegível para o PDM {pdm}")
        escolhidos.append(candidatos[0])
        cobertos |= pdms_de[candidatos[0]]
    total = sum(len(por_cnpj[c]) for c in escolhidos)
    for cnpj in ranking:
        if total >= alvo:
            break
        if cnpj not in escolhidos:
            escolhidos.append(cnpj)
            total += len(por_cnpj[cnpj])
    return escolhidos


def escolher(elegiveis: list[dict], validas: int = TOTAL_VALIDAS, auxiliares: int = 7) -> dict:
    """Escolhe as linhas válidas, as bases das inválidas e o item de fornecedor sem cadastro.

    `auxiliares` são registros de fornecedores das válidas (as 7 inválidas que não dependem de
    fornecedor inexistente). O 8º, do fornecedor que não entra no arquivo de fornecedores, vem
    de fora do conjunto escolhido."""
    por_cnpj = defaultdict(list)
    for r in elegiveis:
        por_cnpj[r["niFornecedor"]].append(r)
    escolhidos = _fornecedores_escolhidos(por_cnpj, validas + auxiliares)
    pool = [r for c in escolhidos for r in por_cnpj[c]]
    ordenado = _rodizio(pool)
    if len(ordenado) < validas + auxiliares:
        raise ErroExportacao(
            f"{len(ordenado)} registros no conjunto, faltam {validas + auxiliares}"
        )
    selecionadas = ordenado[:validas]
    cnpjs_validas = {r["niFornecedor"] for r in selecionadas}
    if {_pdm(r) for r in selecionadas} != set(CATEGORIA_POR_PDM):
        raise ErroExportacao("as linhas válidas não cobrem os 9 PDMs")
    bases = [r for r in ordenado[validas:] if r["niFornecedor"] in cnpjs_validas][:auxiliares]
    if len(bases) < auxiliares:
        raise ErroExportacao(f"{len(bases)} bases para as linhas inválidas, faltam {auxiliares}")
    sem_cadastro = sorted(
        (r for r in elegiveis if r["niFornecedor"] not in cnpjs_validas),
        key=lambda r: (r["niFornecedor"], r["idItemCompra"]),
    )
    if not sem_cadastro:
        raise ErroExportacao("nenhum registro de fornecedor fora das linhas válidas")
    validas_ordenadas = sorted(
        selecionadas, key=lambda r: (list(CATEGORIA_POR_PDM).index(_pdm(r)), r["idItemCompra"])
    )
    return {
        "validas": validas_ordenadas,
        "bases": sorted(bases, key=lambda r: r["idItemCompra"]),
        "sem_cadastro": sem_cadastro[0],
        "fornecedores_escolhidos": len(escolhidos),
        "fornecedores_das_validas": sorted(cnpjs_validas),
    }


def linha_do_registro(registro: dict) -> dict[str, str]:
    return {
        "nome": nome_do_ativo(registro),
        "tipo": "HARDWARE",
        "categoria": CATEGORIA_POR_PDM[_pdm(registro)],
        "fornecedor": _razao(registro),
        "numero_serie": f"CG-{registro['idItemCompra']}-001",
        "chave_licenca": "",
        "data_aquisicao": registro["dataCompra"],
        "valor_compra": str(arredondar(registro["precoUnitario"])),
        "localizacao": "",
        "data_source": FONTE,
        "erro_proposital": "",
    }


def montar_linhas(escolha: dict) -> list[dict[str, str]]:
    """As 100 linhas: as 8 inválidas nas posições de `INVALIDAS`, as 92 válidas nas demais."""
    validas = [linha_do_registro(r) for r in escolha["validas"]]
    posicoes = {numero - 2: item for numero, *item in INVALIDAS}  # índice na lista de dados
    linhas: list[dict[str, str]] = []
    fila = iter(validas)
    for indice in range(TOTAL_LINHAS):
        linhas.append(next(fila) if indice not in posicoes else {})
    serie_repetida = linhas[LINHA_DA_SERIE_REPETIDA - 2]["numero_serie"]
    bases = iter(escolha["bases"])
    for numero, campo, descricao, _ in INVALIDAS:
        base = (
            linha_do_registro(escolha["sem_cadastro"])
            if campo == "fornecedor"
            else linha_do_registro(next(bases))
        )
        base["erro_proposital"] = f"{campo}: {descricao}"
        base[campo] = {
            "nome": "NB",
            "tipo": "PERIFERICO",
            "categoria": "Notebooks",
            "fornecedor": base["fornecedor"],  # já é o fornecedor que não está no arquivo
            "numero_serie": "" if numero == 58 else serie_repetida,
            "data_aquisicao": DATA_FUTURA,
            "valor_compra": "0",
        }[campo]
        linhas[numero - 2] = base
    return linhas


def _csv(caminho: Path, colunas: list[str], linhas: list[dict[str, str]]) -> None:
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def estatisticas_por_pdm(filtrado: dict, validas: list[dict]) -> list[dict]:
    originais = defaultdict(list)
    for r in filtrado["federais"]:
        originais[_pdm(r)].append(r["precoUnitario"])
    usados = defaultdict(list)
    for r in validas:
        usados[_pdm(r)].append(arredondar(r["precoUnitario"]))
    nomes = {_pdm(r): r["nomePdm"] for r in filtrado["federais"]}
    return [
        {
            "pdm": pdm,
            "nome": nomes[pdm],
            "categoria": categoria,
            "originais": len(originais[pdm]),
            "min": min(originais[pdm]),
            "max": max(originais[pdm]),
            "p10": filtrado["faixas"][pdm][0],
            "p90": filtrado["faixas"][pdm][1],
            "usadas": len(usados[pdm]),
            "usado_min": min(usados[pdm]),
            "usado_max": max(usados[pdm]),
        }
        for pdm, categoria in CATEGORIA_POR_PDM.items()
    ]


def _num(valor) -> str:
    return f"{Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)}"


def gerar_leiame(pasta_origem: str, filtrado: dict, escolha: dict) -> str:
    descartes = "\n".join(f"| {rotulo} | {n} |" for rotulo, n in filtrado["descartes"])
    por_pdm = "\n".join(
        f"| {e['pdm']} | {e['nome']} | {e['categoria']} | {e['originais']} | {_num(e['min'])} "
        f"| {_num(e['max'])} | {_num(e['p10'])} | {_num(e['p90'])} | {e['usadas']} "
        f"| {e['usado_min']} | {e['usado_max']} |"
        for e in estatisticas_por_pdm(filtrado, escolha["validas"])
    )
    invalidas = "\n".join(
        f"| {numero} | {campo} | {descricao} | {motivo} |"
        for numero, campo, descricao, motivo in INVALIDAS
    )
    relatorio = "\n".join(f"- linha {n}, campo `{campo}`" for n, campo, *_ in INVALIDAS)
    data = Path(pasta_origem).name
    return f"""# `inventario_demo.csv`: arquivo do Gate 1

Gerado por `python -m etl.exportar_inventario_demo` (`python/etl/exportar_inventario_demo.py`) a
partir de `{pasta_origem}/`, a coleta real do Compras.gov.br de **{data}** (coletor D.1). A data
de geração é a da coleta: o gerador não grava a data de execução, para duas execuções darem
arquivos idênticos. A coleta sanitizada está em `python/tests/fixtures/compras_gov/coleta_{data}/`:
é a coleta real, só com o CPF que segue o nome do microempreendedor na razão social trocado por
zeros (seção "Sanitização" de `python/tests/fixtures/compras_gov/ORIGEM.md`). O teste
`test_exportar_inventario_demo.py` confere que este arquivo é exatamente o que ela gera.

Critério de liberação do Gate 1 (`docs/BACKLOG_E_GATES.md`): **100 linhas processadas, 92 ativos
aceitos e 8 linhas rejeitadas**, com relatório de erros linha a linha.

## O que é cada coluna

Colunas do importador (`docs/spec/pipeline-importacao.md`) mais `data_source = compras_gov` e a
coluna extra `erro_proposital` (o importador ignora colunas que não conhece), preenchida só nas 8
linhas inválidas.

- `numero_serie` = `CG-{{idItemCompra}}-001`: **identificador técnico sintético**, derivado do
  `idItemCompra` do item de compra. A fonte pública não traz número de série real. Não é número
  de fábrica (ADR-011).
- `nome` = `nomePdm` + marca (até 120 caracteres; marca vazia ou só pontuação: só o `nomePdm`).
- `valor_compra` = `precoUnitario` arredondado a 2 casas (ROUND_HALF_UP); `data_aquisicao` =
  `dataCompra`; `tipo` = `HARDWARE`; `localizacao` vazia.
- `categoria` pelo PDM (tabela abaixo); `fornecedor` = `nomeFornecedor`, que precisa existir
  antes (`fornecedores_demo.csv` + `python -m etl.carregar_fornecedores`).

## Metodologia e números

Registros coletados: **{filtrado['coletados']}**. Federais (`esfera = F`): **{len(filtrado['federais'])}**.
Descartes em sequência, sobre os federais (o que se repete é medido sobre todos os coletados):

| Filtro | Descartados |
|---|---|
{descartes}
| **Elegíveis** | **{len(filtrado['elegiveis'])}** |

Fornecedores cuja razão social é o nome de uma pessoa física (microempreendedor individual:
`64.956.713 NOME DA PESSOA`, ou o nome seguido de 11 dígitos) **não entram** no arquivo, por
decisão da equipe. O filtro é só do exportador: a coleta bruta e as fixtures não são alteradas.

Seleção determinística: o menor conjunto de fornecedores (pela ordem de volume, CNPJ como
desempate) que cobre os 9 PDMs e reúne os registros necessários, **{escolha['fornecedores_escolhidos']}
fornecedores escolhidos** ({len(escolha['fornecedores_das_validas'])} aparecem nas 92 linhas válidas). Com ~10
fornecedores não saem as 92 linhas válidas, então a equipe aceitou o mínimo possível. Dentro do conjunto, as
linhas vêm em rodízio entre os PDMs (cobertura antes de volume). Utilizados: 100 registros (92
válidos e 8 bases das inválidas).

### Preço por PDM

Percentis por interpolação linear sobre os registros federais do PDM; "utilizados" são as 92
linhas válidas.

| PDM | CATMAT | Categoria | Federais | Mín. original | Máx. original | P10 | P90 | Válidas | Mín. usado | Máx. usado |
|---|---|---|---|---|---|---|---|---|---|---|
{por_pdm}

## As 8 linhas inválidas (propositais)

Uma por tipo de validação, um erro por linha (8 rejeitadas = 8 erros). Nenhuma "se conserta" com o
tempo: a data futura é 2099-12-31.

| Linha | Campo | Erro inserido | Motivo esperado no relatório |
|---|---|---|---|
{invalidas}

A linha 71 repete o `numero_serie` da linha {LINHA_DA_SERIE_REPETIDA}, que é válida e conta nas 92.
O fornecedor da linha 46 é real, mas fica de fora de `fornecedores_demo.csv`.

Relatório esperado de `GET /importacoes/{{id}}/erros`:

{relatorio}

## Como usar

```bash
cd python
python -m etl.exportar_inventario_demo        # regenera os três arquivos de dataset/demo/
ITAM_API_LOGIN=admin ITAM_API_SENHA=... python -m etl.carregar_fornecedores
# com o seed aplicado (categorias) e logado como ADMIN: POST /api/v1/importacoes com o arquivo
```
"""  # noqa: E501 (tabelas em Markdown)


def gerar(pasta_origem: Path, saida: Path) -> dict:
    filtrado = filtrar(ler_registros(pasta_origem))
    escolha = escolher(filtrado["elegiveis"])
    linhas = montar_linhas(escolha)
    saida.mkdir(parents=True, exist_ok=True)
    _csv(saida / "inventario_demo.csv", COLUNAS, linhas)
    por_cnpj = {r["niFornecedor"]: r for r in escolha["validas"]}
    fornecedores = [
        {"razao_social": _razao(r), "cnpj": cnpj_formatado(cnpj)} for cnpj, r in por_cnpj.items()
    ]
    _csv(
        saida / "fornecedores_demo.csv",
        ["razao_social", "cnpj"],
        sorted(fornecedores, key=lambda f: f["razao_social"]),
    )
    data = re.search(r"\d{4}-\d{2}-\d{2}", pasta_origem.name)  # a cópia em tests/fixtures também
    origem = f"dataset/raw/{FONTE}/{data.group() if data else pasta_origem.name}"
    (saida / "inventario_demo.LEIAME.md").write_text(
        gerar_leiame(origem, filtrado, escolha), encoding="utf-8"
    )
    return {"filtrado": filtrado, "escolha": escolha, "linhas": linhas}


def main() -> int:
    analisador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analisador.add_argument("--raw", type=Path, default=DATASET_DIR / "raw" / FONTE / DATA_COLETA)
    analisador.add_argument("--saida", type=Path, default=DATASET_DIR / "demo")
    argumentos = analisador.parse_args()
    try:
        resultado = gerar(argumentos.raw, argumentos.saida)
    except ErroExportacao as erro:
        print(f"Exportação recusada: {erro}", file=sys.stderr)
        return 1
    print(
        f"{len(resultado['linhas'])} linhas em {argumentos.saida} "
        f"({len(resultado['escolha']['fornecedores_das_validas'])} fornecedores nas válidas)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
