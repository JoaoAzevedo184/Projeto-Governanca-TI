"""Normalização D.6: `dataset/raw/` -> `dataset/processed/`, sem rede e sem banco.

Gera, de forma determinística (duas execuções dão arquivos idênticos, e o dia em que o script roda
não entra em nenhum valor):
- `hardware_compras_gov.csv`: os itens de TI do Compras.gov.br que passam pelos filtros do
  exportador de demonstração (`etl.exportar_inventario_demo.filtrar`), classificados por PDM e
  categoria pelas mesmas regras (`CATEGORIA_POR_PDM`, `nome_do_ativo`); fora pessoa física;
- `software_ciclos_cves.csv`: uma linha por ciclo (versão) de cada produto do endoflife, com data
  de fim de suporte, situação **na data da coleta** (a da pasta de origem) e, quando o cruzamento
  com o NVD é determinístico, as CVEs por severidade CVSS v3;
- `produtos_cruzamento.csv`: por produto, se há correspondência no endoflife, no NVD e nas duas, e
  o motivo de cada não cruzado;
- `LEIAME.md`: fontes, datas, filtros, metodologia, limitações e as contagens.

O cruzamento é conservador: produto e ciclo só se correspondem por igualdade exata, e o NVD só é
consultado para os ciclos que `collectors/config.yaml` lista com CPE e faixa de versão. Sem
correspondência confiável, a linha fica "não cruzada" (colunas de CVE vazias, nunca zero) e entra
na contagem do LEIAME.

endoflife e NVD aqui são só referência: não vão ao banco, não aparecem no sistema e não geram
alerta. Uso (a partir de `python/`): `python -m etl.normalizar`.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from collectors import endoflife, nvd
from etl import exportar_inventario_demo as exportador
from etl.paths import (
    DATASET_DIR,
    ErroReferencia,
    coleta_de_referencia,
    escolher_saida,
    texto_reprodutibilidade,
)

HARDWARE_CSV = "hardware_compras_gov.csv"
SOFTWARE_CSV = "software_ciclos_cves.csv"
PRODUTOS_CSV = "produtos_cruzamento.csv"
LEIAME = "LEIAME.md"

COLUNAS_HARDWARE = [
    "id_item_compra",
    "pdm",
    "nome_pdm",
    "categoria",
    "nome",
    "marca",
    "fornecedor_cnpj",
    "data_compra",
    "preco_unitario",
]
COLUNAS_CVE = [
    "cves_baixa",
    "cves_media",
    "cves_alta",
    "cves_critica",
    "cves_sem_cvss_v3",
    "cves_total",
]
COLUNAS_SOFTWARE = [
    "produto",
    "versao",
    "data_lancamento",
    "data_fim_suporte",
    "situacao_na_coleta",
    "data_coleta_endoflife",
    "cruzamento_nvd",
    *COLUNAS_CVE,
    "motivo_nao_cruzado",
]
COLUNAS_PRODUTOS = [
    "produto",
    "no_endoflife",
    "no_nvd",
    "cruzado",
    "ciclos_endoflife",
    "ciclos_nvd",
    "motivo",
]
MOTIVO_SEM_CPE = "NVD: produto sem CPE configurado em collectors/config.yaml"
MOTIVO_FORA_DA_LISTA = "NVD: ciclo fora da lista consultada em collectors/config.yaml"
MOTIVO_SEM_ENDOFLIFE = "endoflife: sem coleta do produto"
SEVERIDADE_COLUNA = {
    "LOW": "cves_baixa",
    "MEDIUM": "cves_media",
    "HIGH": "cves_alta",
    "CRITICAL": "cves_critica",
}


class ErroNormalizacao(Exception):
    """A coleta ou a configuração não permite normalizar nas condições decididas."""


def data_da_coleta(pasta: Path) -> date:
    """A data da coleta é a da pasta de origem (`raw/<fonte>/AAAA-MM-DD`, ou `coleta_AAAA-MM-DD`
    nas fixtures), nunca a de hoje."""
    achada = re.search(r"\d{4}-\d{2}-\d{2}", pasta.name)
    try:
        if achada:
            return date.fromisoformat(achada.group())
    except ValueError:
        pass
    raise ErroNormalizacao(f"o nome da pasta {pasta} não tem uma data AAAA-MM-DD")


def situacao(eol: object, data_coleta: date) -> str:
    """Situação de um ciclo na data da coleta, pelo campo `eol` do endoflife.

    `eol` é a data do fim do suporte (o próprio dia já conta como fim), `false` (sem data de fim) ou
    `true` (já sem suporte, sem data)."""
    if eol is True:
        return "FORA_DE_SUPORTE"
    if eol is False:
        return "SEM_DATA_DE_FIM"
    if isinstance(eol, str):
        try:
            fim = date.fromisoformat(eol)
        except ValueError:
            raise ErroNormalizacao(f"eol com valor que não é data: {eol!r}") from None
        return "FORA_DE_SUPORTE" if fim <= data_coleta else "EM_SUPORTE"
    raise ErroNormalizacao(f"eol com tipo que a fonte não usa: {eol!r}")


# ---- hardware -------------------------------------------------------------------------------


def hardware(pasta: Path) -> dict:
    """Os itens elegíveis do Compras.gov.br, classificados, e as contagens antes e depois."""
    if not pasta.is_dir():
        raise ErroNormalizacao(f"coleta do Compras.gov.br ausente: {pasta}")
    registros = exportador.ler_registros(pasta)
    if not registros:
        raise ErroNormalizacao(f"coleta do Compras.gov.br vazia: {pasta}")
    filtrado = exportador.filtrar(registros)
    linhas = []
    for r in sorted(filtrado["elegiveis"], key=lambda r: r["idItemCompra"]):
        pdm = int(r["codigoPdm"])
        if pdm not in exportador.CATEGORIA_POR_PDM:
            raise ErroNormalizacao(f"PDM {pdm} sem categoria em CATEGORIA_POR_PDM")
        linhas.append(
            {
                "id_item_compra": str(r["idItemCompra"]),
                "pdm": str(pdm),
                "nome_pdm": r["nomePdm"],
                "categoria": exportador.CATEGORIA_POR_PDM[pdm],
                "nome": exportador.nome_do_ativo(r),
                "marca": r["marca"].strip(),
                "fornecedor_cnpj": r["niFornecedor"],
                "data_compra": r["dataCompra"],
                "preco_unitario": str(exportador.arredondar(r["precoUnitario"])),
            }
        )
    return {
        "linhas": linhas,
        "coletados": filtrado["coletados"],
        "federais": len(filtrado["federais"]),
        "descartes": filtrado["descartes"],
        "por_categoria": Counter(linha["categoria"] for linha in linhas),
    }


# ---- software -------------------------------------------------------------------------------


def _ler_ciclos(pasta: Path, produto: str) -> list[dict] | None:
    arquivo = pasta / f"{produto}.json"
    if not arquivo.exists():
        return None
    ciclos = json.loads(arquivo.read_text(encoding="utf-8"))
    return ciclos or None


def _ler_contagens(pasta: Path, produto: str, ciclo: str) -> dict[str, int] | None:
    """As contagens de um ciclo do NVD, ou `None` se alguma das cinco respostas não existe."""
    contagens: dict[str, int] = {}
    for sufixo in (*nvd.SEVERIDADES, "total"):
        arquivo = pasta / nvd.nome_arquivo(produto, ciclo, None if sufixo == "total" else sufixo)
        if not arquivo.exists():
            return None
        contagens[sufixo] = int(json.loads(arquivo.read_text(encoding="utf-8"))["totalResults"])
    por_severidade = sum(contagens[s] for s in nvd.SEVERIDADES)
    if por_severidade > contagens["total"]:
        raise ErroNormalizacao(
            f"{produto} {ciclo}: soma das severidades ({por_severidade}) maior que o total "
            f"({contagens['total']})"
        )
    return contagens


def _motivo_nvd(ciclos_cfg: list[nvd.Ciclo], contagens: dict[str, dict | None]) -> str:
    if not ciclos_cfg:
        return MOTIVO_SEM_CPE
    faltam = [c.ciclo for c in ciclos_cfg if contagens[c.ciclo] is None]
    if not faltam:
        return ""
    rotulo = "o ciclo" if len(faltam) == 1 else "os ciclos"
    return f"NVD: coleta ausente ou incompleta para {rotulo} {', '.join(faltam)}"


def software(
    pasta_endoflife: Path,
    pasta_nvd: Path,
    cfg_endoflife: endoflife.Configuracao,
    cfg_nvd: nvd.Configuracao,
) -> dict:
    """Linhas por ciclo e a situação de cada produto nas duas fontes."""
    for pasta in (pasta_endoflife, pasta_nvd):
        if not pasta.is_dir():
            raise ErroNormalizacao(f"coleta ausente: {pasta}")
    data_eol = data_da_coleta(pasta_endoflife)
    do_nvd = {p.produto: p.ciclos for p in cfg_nvd.produtos}
    nomes = [*cfg_endoflife.produtos, *(p for p in do_nvd if p not in cfg_endoflife.produtos)]
    linhas: list[dict[str, str]] = []
    produtos: list[dict[str, str]] = []
    for produto in nomes:
        ciclos_eol = _ler_ciclos(pasta_endoflife, produto)
        ciclos_cfg = do_nvd.get(produto, [])
        contagens = {c.ciclo: _ler_contagens(pasta_nvd, produto, c.ciclo) for c in ciclos_cfg}
        if ciclos_eol is not None:
            existentes = {c["cycle"] for c in ciclos_eol}
            for c in ciclos_cfg:
                if c.ciclo not in existentes:
                    raise ErroNormalizacao(
                        f"{produto} {c.ciclo}: ciclo configurado no NVD não existe no endoflife"
                    )
        motivo_nvd = _motivo_nvd(ciclos_cfg, contagens)
        no_eol, no_nvd = ciclos_eol is not None, not motivo_nvd
        motivos = [m for m in ("" if no_eol else MOTIVO_SEM_ENDOFLIFE, motivo_nvd) if m]
        produtos.append(
            {
                "produto": produto,
                "no_endoflife": "SIM" if no_eol else "NAO",
                "no_nvd": "SIM" if no_nvd else "NAO",
                "cruzado": "SIM" if no_eol and no_nvd else "NAO",
                "ciclos_endoflife": str(len(ciclos_eol or [])),
                "ciclos_nvd": str(len(ciclos_cfg) if no_nvd else 0),
                "motivo": "; ".join(motivos),
            }
        )
        for versao in sorted(
            ciclos_eol or [], key=lambda v: (v.get("releaseDate") or "", v["cycle"]), reverse=True
        ):
            dos_cves = contagens.get(versao["cycle"]) if no_nvd else None
            linha = {
                "produto": produto,
                "versao": versao["cycle"],
                "data_lancamento": versao.get("releaseDate") or "",
                "data_fim_suporte": versao["eol"] if isinstance(versao["eol"], str) else "",
                "situacao_na_coleta": situacao(versao["eol"], data_eol),
                "data_coleta_endoflife": data_eol.isoformat(),
                "cruzamento_nvd": "CRUZADO" if dos_cves else "NAO_CRUZADO",
                **dict.fromkeys(COLUNAS_CVE, ""),
                "motivo_nao_cruzado": "",
            }
            if dos_cves:
                for severidade, coluna in SEVERIDADE_COLUNA.items():
                    linha[coluna] = str(dos_cves[severidade])
                total = dos_cves["total"]
                linha["cves_total"] = str(total)
                linha["cves_sem_cvss_v3"] = str(total - sum(dos_cves[s] for s in nvd.SEVERIDADES))
            else:
                linha["motivo_nao_cruzado"] = motivo_nvd or MOTIVO_FORA_DA_LISTA
            linhas.append(linha)
    return {"linhas": linhas, "produtos": produtos, "data_endoflife": data_eol}


# ---- saída ----------------------------------------------------------------------------------


def _csv(caminho: Path, colunas: list[str], linhas: list[dict[str, str]]) -> None:
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def _tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    topo = f"| {' | '.join(cabecalho)} |\n|{'---|' * len(cabecalho)}"
    return "\n".join([topo, *(f"| {' | '.join(linha)} |" for linha in linhas)])


def gerar_leiame(
    pastas: dict[str, Path],
    hw: dict,
    sw: dict,
    cfg_endoflife: endoflife.Configuracao,
    cfg_nvd: nvd.Configuracao,
) -> str:
    produtos = sw["produtos"]
    nao_cruzados = [p for p in produtos if p["cruzado"] == "NAO"]
    versoes = sw["linhas"]
    cruzadas = [r for r in versoes if r["cruzamento_nvd"] == "CRUZADO"]
    datas = {fonte: data_da_coleta(pasta).isoformat() for fonte, pasta in pastas.items()}
    descartes = _tabela(
        ["Filtro", "Descartados"], [[rotulo, str(n)] for rotulo, n in hw["descartes"]]
    )
    categorias = _tabela(
        ["Categoria", "Registros"], [[c, str(n)] for c, n in sorted(hw["por_categoria"].items())]
    )
    ciclos_nvd = _tabela(
        ["Produto", "Ciclo", "CPE", "Versão inicial (inclusive)", "Versão final (exclusive)"],
        [
            [f"`{p.produto}`", c.ciclo, f"`{c.cpe}`", c.de or "-", c.ate or "-"]
            for p in cfg_nvd.produtos
            for c in p.ciclos
        ],
    )
    motivos = _tabela(
        ["Produto", "Motivo"], [[f"{p['produto']}", p["motivo"]] for p in nao_cruzados]
    )
    contagem = _tabela(
        ["Contagem do D.6", "Produtos"],
        [
            ["Produtos analisados", f"**{len(produtos)}**"],
            [
                "Com correspondência no endoflife",
                f"**{sum(p['no_endoflife'] == 'SIM' for p in produtos)}**",
            ],
            ["Com correspondência no NVD", f"**{sum(p['no_nvd'] == 'SIM' for p in produtos)}**"],
            [
                "Com correspondência nas duas fontes",
                f"**{sum(p['cruzado'] == 'SIM' for p in produtos)}**",
            ],
            ["Não cruzados", f"**{len(nao_cruzados)}**"],
        ],
    )
    ciclos_cfg = [c for p in cfg_nvd.produtos for c in p.ciclos]
    zeros = [f"`{r['produto']}` {r['versao']}" for r in cruzadas if r["cves_total"] == "0"]
    sobre_zeros = ""
    if zeros:
        lista = zeros[0] if len(zeros) == 1 else f"{', '.join(zeros[:-1])} e {zeros[-1]}"
        sobre_zeros = f" Na coleta de {datas['nvd']}, tiveram contagem zero: {lista}."
        if any(r["produto"] == "nginx" for r in cruzadas if r["cves_total"] == "0"):
            sobre_zeros += (
                " Para o nginx, a conferência manual com o CPE antigo `cpe:2.3:a:nginx:nginx`, que "
                "também deu 0, está em `python/tests/fixtures/nvd/ORIGEM.md`."
            )
    como_ler = (
        "### Como ler as contagens do NVD\n\n"
        "- O identificador de cada produto no NVD (o CPE) e a faixa de versão de cada ciclo foram "
        "**definidos manualmente** em `python/collectors/config.yaml`; nada foi encontrado nem "
        "deduzido por correspondência de nomes.\n"
        f"- Só os **{len(ciclos_cfg)} ciclos** da tabela acima foram consultados no NVD. As demais "
        "versões ficaram fora **por decisão** de limitar o volume, não por falha de "
        "correspondência: "
        "o NVD não foi perguntado sobre elas, e o motivo de cada uma está em "
        "`motivo_nao_cruzado`.\n"
        "- Contagem **zero** significa **nenhuma CVE encontrada por esta consulta**, não ausência "
        "de vulnerabilidades: depende do CPE e da faixa de versão escritos na configuração e do "
        "que o NVD tinha associado a eles na data da coleta." + sobre_zeros
    )
    produtos_pesquisados = ", ".join(f"`{p}`" for p in cfg_endoflife.produtos)
    return f"""# `dataset/processed/`: referência normalizada (D.6)

Gerado por `python -m etl.normalizar` (`python/etl/normalizar.py`) a partir de
`dataset/raw/compras_gov/{datas['compras_gov']}/`, `dataset/raw/endoflife/{datas['endoflife']}/` e
`dataset/raw/nvd/{datas['nvd']}/`. A data de cada coleta é a da pasta de origem: o gerador não grava
a data de execução, e duas execuções dão arquivos idênticos. As coletas gravadas estão em
`python/tests/fixtures/` (ver os `ORIGEM.md`), e o teste `test_normalizar.py` confere que estes
arquivos são exatamente o que elas geram, sem rede.

**endoflife e NVD não são carregados no banco, não aparecem nas telas do ITAM e não geram alertas na versão atual.**
Só o dataset do Compras.gov.br usado na demonstração (`dataset/demo/`) é carregado no banco, pelo seed e pela importação. Os arquivos desta pasta são referência reproduzível, não entrada do sistema.

## Fontes

| Fonte | Endereço | Coleta | O que entra aqui |
|---|---|---|---|
| Compras.gov.br | https://dadosabertos.compras.gov.br (`/modulo-pesquisa-preco/1_consultarMaterial`) | {datas['compras_gov']} | Itens de TI de 9 PDMs do CATMAT |
| endoflife.date | https://endoflife.date (`/api/<produto>.json`) | {datas['endoflife']} | Ciclos de vida e fim de suporte |
| NVD (NIST) | https://services.nvd.nist.gov (`/rest/json/cves/2.0`) | {datas['nvd']} | Contagem de CVEs por ciclo e severidade |

Produtos pesquisados no endoflife (8): {produtos_pesquisados}. O slug `apache` do endoflife
redireciona (HTTP 301) e o coletor não segue redirecionamento, então o Tomcat o substituiu.

## `hardware_compras_gov.csv`: hardware do Compras.gov.br

Normalizado e classificado com as funções e os filtros do exportador de demonstração
(`etl/exportar_inventario_demo.py`), sem regra duplicada: só esfera federal; fora identificador de
fornecedor estrangeiro, razão social de pessoa física (microempreendedor), CNPJ com mais de uma razão
social e vice-versa, item repetido e preço fora da faixa P10-P90 do PDM. A categoria vem do PDM
(`CATEGORIA_POR_PDM`); PDM sem categoria é erro, não linha sem classificar. O arquivo não tem
número de série: o `numero_serie` técnico do arquivo de demonstração é um identificador sintético.
O fornecedor aparece só pelo CNPJ: a razão social foi omitida de propósito (minimização de dados),
porque a de empresário individual pode ser o nome do titular.

Registros coletados: **{hw['coletados']}**. Federais: **{hw['federais']}**. Descartes em sequência, sobre
os federais (o que se repete é medido sobre todos os coletados):

{descartes}

| Registros de hardware normalizados | **{len(hw['linhas'])}** |
|---|---|

{categorias}

## `software_ciclos_cves.csv` e `produtos_cruzamento.csv`: ciclo de vida e CVEs

Uma linha por ciclo (versão) de cada produto do endoflife: data de lançamento, data de fim de
suporte e situação **na data da coleta** do endoflife ({datas['endoflife']}): `EM_SUPORTE`,
`FORA_DE_SUPORTE` (a data de fim já chegou, inclusive o próprio dia, ou o endoflife marca `true`) ou
`SEM_DATA_DE_FIM` (o endoflife marca `false`). A situação não depende do dia em que o script roda.

As colunas de CVE (`cves_baixa`, `cves_media`, `cves_alta`, `cves_critica`, `cves_sem_cvss_v3`,
`cves_total`) vêm do NVD, só para os ciclos da tabela abaixo; `cves_total` conta todas as CVEs do
ciclo e `cves_sem_cvss_v3` é o total menos as quatro severidades (CVEs que a consulta por severidade CVSS v3 não alcança: sem análise do NVD ou sem métrica v3.x).

{ciclos_nvd}

{como_ler}

{contagem}

| Versões (ciclos) do endoflife | **{len(versoes)}** |
|---|---|
| Versões cruzadas com o NVD | **{len(cruzadas)}** |

Produtos não cruzados, com o motivo:

{motivos}

## Metodologia

- **Cruzamento conservador.** Produto e ciclo só se correspondem por igualdade exata de nome. O NVD só
  é consultado para o CPE e a faixa de versão que `python/collectors/config.yaml` escreve para cada
  ciclo; nada é deduzido por semelhança. Sem correspondência confiável o ciclo fica
  `NAO_CRUZADO`, com o motivo em `motivo_nao_cruzado`, e as colunas de CVE ficam **vazias, nunca zero**.
- **Um ciclo do NVD que não existe no endoflife é erro de configuração**, não linha ignorada.
- **Contagens por severidade** são `totalResults` de consultas de um registro por severidade CVSS v3
  (`cvssV3Severity`) e por ciclo, mais uma sem filtro (o total).
- **Determinismo.** Ordem fixa (produtos da configuração; ciclos pela data de lançamento, do mais
  novo ao mais antigo), sem data de execução, CSV com fim de linha `\\n`.

{texto_reprodutibilidade()}
## Limitações

- É uma referência de {len(cfg_endoflife.produtos)} produtos de software corporativo comuns, não um catálogo.
- As contagens do NVD são as da data da coleta ({datas['nvd']}) e mudam todo dia na fonte; refazer a coleta
  gera valores diferentes. Contam CVEs que o NVD associa ao CPE e à faixa de versão escritos na
  configuração; não medem exposição de nenhum ativo.
- A severidade é a do CVSS v3.x; CVEs que não têm essa métrica (por exemplo, só CVSS v2 ou v4, ou ainda sem análise do NVD) aparecem apenas no total, e o arquivo não distingue o motivo.
- O endoflife publica `eol` por ciclo, não por versão de correção: o ciclo `16` do PostgreSQL cobre
  todas as `16.x`.
- Nenhum dado daqui é vinculado a ativo do ITAM, e não há alerta de ciclo de vida nem de CVE.
"""  # noqa: E501 (tabelas e texto em Markdown)


def gerar(
    compras: Path,
    pasta_endoflife: Path,
    pasta_nvd: Path,
    saida: Path,
    cfg_endoflife: endoflife.Configuracao | None = None,
    cfg_nvd: nvd.Configuracao | None = None,
) -> dict:
    cfg_endoflife = cfg_endoflife or endoflife.carregar_configuracao()
    cfg_nvd = cfg_nvd or nvd.carregar_configuracao()
    hw = hardware(compras)
    sw = software(pasta_endoflife, pasta_nvd, cfg_endoflife, cfg_nvd)
    leiame = gerar_leiame(
        {"compras_gov": compras, "endoflife": pasta_endoflife, "nvd": pasta_nvd},
        hw,
        sw,
        cfg_endoflife,
        cfg_nvd,
    )
    saida.mkdir(parents=True, exist_ok=True)  # só depois de tudo calculado: erro não deixa pasta
    _csv(saida / HARDWARE_CSV, COLUNAS_HARDWARE, hw["linhas"])
    _csv(saida / SOFTWARE_CSV, COLUNAS_SOFTWARE, sw["linhas"])
    _csv(saida / PRODUTOS_CSV, COLUNAS_PRODUTOS, sw["produtos"])
    (saida / LEIAME).write_text(leiame, encoding="utf-8")
    return {"hardware": hw, "software": sw}


FONTES = ("compras_gov", "endoflife", "nvd")


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ajuda = "outra coleta que não a de referência do config.yaml (exige --saida)"
    analisador.add_argument("--compras", type=Path, help=ajuda)
    analisador.add_argument("--endoflife", type=Path, help=ajuda)
    analisador.add_argument("--nvd", type=Path, help=ajuda)
    analisador.add_argument("--saida", type=Path, help="padrão: dataset/processed/ (a versionada)")
    analisador.add_argument(
        "--se-houver-referencia",
        action="store_true",
        help="sem as coletas de referência em dataset/raw/, avisa e sai com 0, sem gravar nada",
    )
    argumentos = analisador.parse_args(argv)
    informadas = {
        fonte: pasta
        for fonte, pasta in zip(
            FONTES, (argumentos.compras, argumentos.endoflife, argumentos.nvd), strict=True
        )
        if pasta is not None
    }
    try:
        saida = escolher_saida(informadas, argumentos.saida, DATASET_DIR / "processed")
        padrao = {
            fonte: DATASET_DIR / "raw" / fonte / coleta_de_referencia(fonte)
            for fonte in FONTES
            if fonte not in informadas
        }
        ausentes = [p for p in padrao.values() if not p.is_dir()]
        if ausentes and argumentos.se_houver_referencia:
            print(
                "Coleta de referência ausente em dataset/raw/ "
                f"({', '.join(str(p) for p in ausentes)}): arquivos versionados mantidos."
            )
            return 0
        if ausentes:
            raise ErroNormalizacao(
                f"coleta de referência ausente: {', '.join(str(p) for p in ausentes)} (colete de "
                "novo, ou informe outra coleta com --compras/--endoflife/--nvd e --saida; ver "
                "docs/guia/coleta-de-dados.md)"
            )
        pastas = {**padrao, **informadas}
        resultado = gerar(pastas["compras_gov"], pastas["endoflife"], pastas["nvd"], saida)
    except (ErroNormalizacao, ErroReferencia) as erro:
        print(f"Normalização recusada: {erro}", file=sys.stderr)
        return 1
    print(
        f"{len(resultado['hardware']['linhas'])} registros de hardware, "
        f"{len(resultado['software']['linhas'])} versões de software e "
        f"{len(resultado['software']['produtos'])} produtos em {saida}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
