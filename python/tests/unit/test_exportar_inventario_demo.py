"""Exportador do arquivo do Gate 1 (D.2): regras puras e geração a partir da coleta real.

Sem rede. As regras puras usam registros mínimos montados no teste (só os campos que a regra
lê); a geração de ponta a ponta usa a coleta real sanitizada (ver `ORIGEM.md`) em
`tests/fixtures/compras_gov/coleta_2026-10-05/` e compara com o que está versionado em
`dataset/demo/`.
"""

import csv
import re
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from etl import exportar_inventario_demo as exportador
from etl.exportar_inventario_demo import ErroExportacao

RAIZ = Path(__file__).resolve().parents[3]
COLETA = Path(__file__).resolve().parents[1] / "fixtures" / "compras_gov" / "coleta_2026-10-05"
DEMO = RAIZ / "dataset" / "demo"


def _registro(**ajustes):
    base = {
        "esfera": "F",
        "niFornecedor": "11111111000111",
        "nomeFornecedor": "ALFA LTDA",
        "idCompra": 1,
        "idCompraItem": "1-1",
        "idItemCompra": 1,
        "codigoPdm": "8435",
        "nomePdm": "NOTEBOOK",
        "marca": "DELL",
        "precoUnitario": 100.0,
        "dataCompra": "2026-01-10",
    }
    return {**base, **ajustes}


# ---- regras puras --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (442.584, "442.58"),  # abaixo da metade: para baixo
        (442.585, "442.59"),  # na metade: para cima (ROUND_HALF_UP)
        (2.675, "2.68"),  # em binário seria 2.67499...; vale o decimal escrito
        (10.0, "10.00"),
        (0.004, "0.00"),
    ],
)
def test_arredonda_a_2_casas_com_meio_para_cima(valor, esperado):
    assert exportador.arredondar(valor) == Decimal(esperado)


def test_percentis_10_e_90_por_interpolacao_linear():
    # 1..11: a posição do P10 é 0,1 x 10 = 1 (valor 2); a do P90, 0,9 x 10 = 9 (valor 10).
    assert exportador.percentis([float(n) for n in range(1, 12)]) == (2.0, 10.0)
    assert exportador.percentis([7.0]) == (7.0, 7.0)  # um só registro: a faixa é ele mesmo
    # 1, 2, 3, 4: P10 em 0,3 (1,3) e P90 em 2,7 (3,7)
    p10, p90 = exportador.percentis([1.0, 2.0, 3.0, 4.0])
    assert (round(p10, 6), round(p90, 6)) == (1.3, 3.7)


@pytest.mark.parametrize(
    ("marca", "esperado"),
    [
        ("DELL", "NOTEBOOK DELL"),
        ("  Dell   Inc  ", "NOTEBOOK Dell Inc"),
        ("", "NOTEBOOK"),
        ("-", "NOTEBOOK"),
        (".", "NOTEBOOK"),
        ("   ", "NOTEBOOK"),
    ],
)
def test_nome_junta_pdm_e_marca_sem_espacos_sobrando(marca, esperado):
    assert exportador.nome_do_ativo(_registro(marca=marca)) == esperado


def test_nome_passa_no_maximo_120_caracteres_e_nao_termina_em_espaco():
    nome = exportador.nome_do_ativo(_registro(nomePdm="N" * 100, marca="M" * 10 + " " + "X" * 30))

    assert len(nome) <= 120 and nome == nome.rstrip()
    assert nome.startswith("N" * 100 + " MMMMMMMMMM")


@pytest.mark.parametrize(
    ("razao", "pessoa_fisica"),
    [
        ("64.956.713 IAGO BARROS NOOBLATH", True),  # MEI: prefixo do CNPJ + nome da pessoa
        ("49.981.448 FERNANDA SOUSA CAMPOS", True),
        ("FULANO DE TAL 00000000000", True),  # formato antigo: nome + 11 dígitos
        ("BELTRANO DA SILVA 00000000000", True),
        ("1 BIT GESTAO E CONSULTORIA LTDA", False),  # dígito no nome da empresa não conta
        ("AF3 COMERCIAL LTDA", False),
        ("7LAN COMERCIO E SERVICOS LTDA", False),
        ("O2 SOLUCOES EM TECNOLOGIA DIGITAL LTDA", False),
        ("FERREIRA B2G LTDA", False),
        ("ALFA COMERCIO LTDA", False),
        ("64.956.713/0001-06 EMPRESA LTDA", False),  # CNPJ completo com barra: não é MEI
        ("EMPRESA 1234567890123 LTDA", False),  # 13 dígitos não é CPF
    ],
)
def test_reconhece_razao_social_de_pessoa_fisica(razao, pessoa_fisica):
    assert exportador.razao_de_pessoa_fisica(razao) is pessoa_fisica


def test_cnpj_formatado_com_mascara_de_18_caracteres():
    assert exportador.cnpj_formatado("04602789000101") == "04.602.789/0001-01"


def test_cada_filtro_descarta_o_que_diz_e_a_contagem_e_em_sequencia():
    registros = [
        _registro(idItemCompra=1, idCompraItem="a", precoUnitario=100.0),
        _registro(idItemCompra=2, idCompraItem="b", precoUnitario=200.0),
        _registro(idItemCompra=3, idCompraItem="c", precoUnitario=300.0),
        _registro(idItemCompra=4, esfera="M", idCompraItem="d"),  # não federal
        _registro(  # identificador estrangeiro
            idItemCompra=5, idCompraItem="e", niFornecedor="US994838687", nomeFornecedor="X LLC"
        ),
        _registro(  # CNPJ com duas razões sociais (esta e a ALFA LTDA)
            idItemCompra=6, idCompraItem="f", nomeFornecedor="ALFA COMERCIO LTDA"
        ),
        _registro(  # razão social com dois CNPJs (esta e a de BETA, abaixo)
            idItemCompra=7,
            idCompraItem="g",
            niFornecedor="22222222000122",
            nomeFornecedor="BETA LTDA",
        ),
        _registro(
            idItemCompra=8,
            idCompraItem="h",
            niFornecedor="33333333000133",
            nomeFornecedor="BETA LTDA",
        ),
        _registro(  # (idCompra, idCompraItem) repetido
            idItemCompra=9, idCompraItem="a", niFornecedor="44444444000144", nomeFornecedor="GAMA"
        ),
    ]

    resultado = exportador.filtrar(registros)

    descartes = dict(resultado["descartes"])
    assert resultado["coletados"] == 9 and len(resultado["federais"]) == 8
    assert descartes["identificador de fornecedor estrangeiro"] == 1
    assert descartes["CNPJ com mais de uma razão social"] == 4  # ALFA LTDA x3 e ALFA COMERCIO
    assert descartes["razão social com mais de um CNPJ"] == 2
    assert descartes["item com (idCompra, idCompraItem) repetido"] == 1
    assert resultado["elegiveis"] == []  # tudo caiu em algum filtro antes da faixa de preço


def test_faixa_de_preco_mantem_so_o_que_esta_entre_p10_e_p90_inclusive():
    precos = [float(n) for n in range(1, 12)]  # P10 = 2, P90 = 10
    registros = [
        _registro(
            idItemCompra=n,
            idCompraItem=str(n),
            niFornecedor=f"{n:014d}",
            nomeFornecedor=f"F{n}",
            precoUnitario=p,
        )
        for n, p in enumerate(precos, start=1)
    ]

    elegiveis = exportador.filtrar(registros)["elegiveis"]

    assert [r["precoUnitario"] for r in elegiveis] == [float(n) for n in range(2, 11)]


def test_a_faixa_vale_por_pdm_e_so_sobre_os_federais():
    federais_pdm_a = [
        _registro(idItemCompra=n, idCompraItem=f"a{n}", nomeFornecedor="ALFA LTDA", precoUnitario=p)
        for n, p in enumerate((10.0, 20.0, 30.0), start=1)
    ]
    federal_pdm_b = _registro(
        idItemCompra=9, idCompraItem="b", codigoPdm="6661", nomePdm="MICRO", precoUnitario=5000.0
    )
    municipal_a = _registro(  # muito caro, mas municipal: não entra no percentil do PDM
        idItemCompra=10, idCompraItem="m", esfera="M", precoUnitario=1_000_000.0
    )

    resultado = exportador.filtrar([*federais_pdm_a, federal_pdm_b, municipal_a])

    assert resultado["faixas"][8435] == (12.0, 28.0)
    # do PDM A só o 20 (10 e 30 ficam fora da faixa); o PDM B tem um registro, que é a própria faixa
    assert [r["precoUnitario"] for r in resultado["elegiveis"]] == [20.0, 5000.0]
    assert 6661 in resultado["faixas"] and 1_000_000.0 not in resultado["faixas"][8435]


def test_escolher_recusa_quando_um_pdm_nao_tem_registro():
    with pytest.raises(ErroExportacao, match="PDM 8435"):
        exportador.escolher([])


def test_escolher_recusa_quando_as_validas_nao_cobrem_os_9_pdms():
    elegiveis = [
        _registro(
            idItemCompra=n,
            idCompraItem=str(n),
            niFornecedor=f"{n:014d}",
            nomeFornecedor=f"F{n}",
            codigoPdm=str(pdm),
        )
        for n, pdm in enumerate(exportador.CATEGORIA_POR_PDM, start=1)
    ]

    with pytest.raises(ErroExportacao, match="9 PDMs"):
        exportador.escolher(elegiveis, validas=5, auxiliares=0)


def test_escolher_recusa_quando_faltam_registros():
    elegiveis = [_registro(codigoPdm=str(pdm)) for pdm in exportador.CATEGORIA_POR_PDM]

    with pytest.raises(ErroExportacao, match="faltam"):
        exportador.escolher(elegiveis, validas=9, auxiliares=7)


# ---- ponta a ponta sobre a coleta real ---------------------------------------------------


@pytest.fixture(scope="module")
def gerado(tmp_path_factory):
    saida = tmp_path_factory.mktemp("demo")
    return exportador.gerar(COLETA, saida) | {"saida": saida}


def _linhas(arquivo: Path) -> list[dict[str, str]]:
    with arquivo.open(encoding="utf-8", newline="") as aberto:
        return list(csv.DictReader(aberto))


def test_os_numeros_do_filtro_na_coleta_real(gerado):
    filtrado = gerado["filtrado"]

    assert filtrado["coletados"] == 1705
    assert len(filtrado["federais"]) == 702
    assert filtrado["descartes"] == [
        ("identificador de fornecedor estrangeiro", 1),
        ("razão social de pessoa física (microempreendedor)", 61),
        ("CNPJ com mais de uma razão social", 15),
        ("razão social com mais de um CNPJ", 26),
        ("item com (idCompra, idCompraItem) repetido", 8),
        ("preço fora da faixa P10-P90 do PDM", 124),
    ]
    assert len(filtrado["elegiveis"]) == 467


def test_o_arquivo_tem_100_linhas_92_validas_e_as_8_invalidas_nas_posicoes_decididas(gerado):
    linhas = _linhas(gerado["saida"] / "inventario_demo.csv")

    assert len(linhas) == 100
    propositais = [i + 2 for i, linha in enumerate(linhas) if linha["erro_proposital"]]
    assert propositais == [7, 18, 31, 46, 58, 71, 84, 97]  # numero_linha do relatório
    assert list(linhas[0]) == exportador.COLUNAS


def test_as_92_validas_seguem_as_regras_decididas(gerado):
    validas = [
        r for r in _linhas(gerado["saida"] / "inventario_demo.csv") if not r["erro_proposital"]
    ]
    por_serie = {f"CG-{r['idItemCompra']}-001": r for r in gerado["filtrado"]["elegiveis"]}
    faixas = gerado["filtrado"]["faixas"]

    assert len(validas) == 92
    assert {r["tipo"] for r in validas} == {"HARDWARE"}
    assert {r["data_source"] for r in validas} == {"compras_gov"}
    assert {r["localizacao"] for r in validas} == {""}
    assert all(re.fullmatch(r"CG-\d+-001", r["numero_serie"]) for r in validas)
    assert len({r["numero_serie"] for r in validas}) == 92
    assert all(3 <= len(r["nome"]) <= 120 and r["nome"] == r["nome"].strip() for r in validas)
    registros = [por_serie[r["numero_serie"]] for r in validas]  # cada linha vem de um elegível
    assert {int(x["codigoPdm"]) for x in registros} == set(exportador.CATEGORIA_POR_PDM)
    for linha, registro in zip(validas, registros, strict=True):
        pdm = int(registro["codigoPdm"])
        assert linha["categoria"] == exportador.CATEGORIA_POR_PDM[pdm]
        assert linha["fornecedor"] == registro["nomeFornecedor"].strip()
        assert linha["data_aquisicao"] == registro["dataCompra"]
        assert faixas[pdm][0] <= registro["precoUnitario"] <= faixas[pdm][1]
        assert Decimal(linha["valor_compra"]) == exportador.arredondar(registro["precoUnitario"])
        assert date.fromisoformat(linha["data_aquisicao"]) <= date(2026, 10, 5)


def test_cada_invalida_tem_um_erro_so_e_o_valor_inserido(gerado):
    linhas = _linhas(gerado["saida"] / "inventario_demo.csv")
    validas = _linhas_validas = [r for r in linhas if not r["erro_proposital"]]
    nomes_de_fornecedores = {
        f["razao_social"] for f in _linhas(gerado["saida"] / "fornecedores_demo.csv")
    }
    por_linha = {i + 2: r for i, r in enumerate(linhas)}

    assert por_linha[7]["nome"] == "NB"
    assert por_linha[18]["tipo"] == "PERIFERICO"
    assert por_linha[31]["categoria"] == "Notebooks"
    assert por_linha[46]["fornecedor"] not in nomes_de_fornecedores
    assert por_linha[58]["numero_serie"] == ""
    assert por_linha[71]["numero_serie"] == por_linha[5]["numero_serie"]  # a 5 é válida
    assert por_linha[84]["data_aquisicao"] == "2099-12-31"
    assert por_linha[97]["valor_compra"] == "0"
    assert por_linha[5]["erro_proposital"] == "" and len(validas) == 92
    # fora do campo estragado, a linha é igual às válidas: fornecedor cadastrado, série CG-...
    for numero in (7, 18, 31, 58, 84, 97):
        assert por_linha[numero]["fornecedor"] in nomes_de_fornecedores


def test_fornecedores_demo_sao_os_das_linhas_validas_com_cnpj_formatado(gerado):
    linhas = _linhas(gerado["saida"] / "inventario_demo.csv")
    fornecedores = _linhas(gerado["saida"] / "fornecedores_demo.csv")

    das_validas = {r["fornecedor"] for r in linhas if not r["erro_proposital"]}
    assert {f["razao_social"] for f in fornecedores} == das_validas
    assert len(fornecedores) == 17
    assert all(re.fullmatch(r"\d\d\.\d{3}\.\d{3}/\d{4}-\d\d", f["cnpj"]) for f in fornecedores)
    assert len({f["cnpj"] for f in fornecedores}) == 17


def test_nenhum_fornecedor_do_arquivo_e_pessoa_fisica(gerado):
    linhas = _linhas(gerado["saida"] / "inventario_demo.csv")
    fornecedores = _linhas(gerado["saida"] / "fornecedores_demo.csv")

    nomes = {f["razao_social"] for f in fornecedores} | {r["fornecedor"] for r in linhas}
    assert [n for n in nomes if exportador.razao_de_pessoa_fisica(n)] == []
    # a coleta tem esses fornecedores: o filtro os tirou do arquivo, não da coleta
    coletados = {r["nomeFornecedor"].strip() for r in exportador.ler_registros(COLETA)}
    assert len([n for n in coletados if exportador.razao_de_pessoa_fisica(n)]) > 70


def test_duas_geracoes_dao_arquivos_identicos(gerado, tmp_path):
    exportador.gerar(COLETA, tmp_path)

    for nome in ("inventario_demo.csv", "fornecedores_demo.csv", "inventario_demo.LEIAME.md"):
        assert (tmp_path / nome).read_bytes() == (gerado["saida"] / nome).read_bytes()


@pytest.mark.parametrize(
    "nome", ["inventario_demo.csv", "fornecedores_demo.csv", "inventario_demo.LEIAME.md"]
)
def test_o_que_esta_versionado_em_dataset_demo_e_o_que_a_coleta_gera(gerado, nome):
    assert (DEMO / nome).read_bytes() == (gerado["saida"] / nome).read_bytes()


def test_leiame_traz_a_metodologia_os_numeros_e_as_8_invalidas(gerado):
    texto = (gerado["saida"] / "inventario_demo.LEIAME.md").read_text(encoding="utf-8")

    assert "Registros coletados: **1705**" in texto and "Federais (`esfera = F`): **702**" in texto
    assert "| **Elegíveis** | **467** |" in texto
    assert "identificador técnico sintético" in texto
    assert "dataset/raw/compras_gov/2026-10-05/" in texto
    for pdm in exportador.CATEGORIA_POR_PDM:
        assert f"| {pdm} |" in texto  # uma linha de preço por PDM
    for numero, campo, *_ in exportador.INVALIDAS:
        assert f"- linha {numero}, campo `{campo}`" in texto


def test_main_gera_os_tres_arquivos_e_sai_com_0(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["x", "--raw", str(COLETA), "--saida", str(tmp_path)])

    codigo = exportador.main()

    assert codigo == 0 and "100 linhas" in capsys.readouterr().out
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "fornecedores_demo.csv",
        "inventario_demo.LEIAME.md",
        "inventario_demo.csv",
    ]


def test_main_recusa_coleta_vazia_sem_gravar_nada(tmp_path, monkeypatch, capsys):
    raw, saida = tmp_path / "raw", tmp_path / "saida"
    raw.mkdir()
    monkeypatch.setattr(sys, "argv", ["x", "--raw", str(raw), "--saida", str(saida)])

    codigo = exportador.main()

    assert codigo == 1
    assert "Exportação recusada" in capsys.readouterr().err
    assert not saida.exists()
