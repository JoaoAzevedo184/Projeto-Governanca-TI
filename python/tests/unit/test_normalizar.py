"""Normalização D.6 (`etl/normalizar.py`): `dataset/raw/` -> `dataset/processed/`, sem rede.

A geração de ponta a ponta usa as coletas reais gravadas em `tests/fixtures/` (Compras.gov.br de
2026-10-05, endoflife e NVD de 2026-10-06; ver os `ORIGEM.md`) e confere o que está versionado em
`dataset/processed/`. Os casos de borda usam entradas mínimas montadas no teste (dados de teste
do normalizador, não respostas de API). Nenhum teste usa rede: o `socket` fica bloqueado.
"""

import csv
import json
import re
import shutil
import socket
from datetime import date
from pathlib import Path

import pytest

from collectors import endoflife, nvd
from collectors.nvd import Ciclo, Produto
from etl import exportar_inventario_demo as exportador
from etl import normalizar
from etl.normalizar import ErroNormalizacao

RAIZ = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
COMPRAS = FIXTURES / "compras_gov" / "coleta_2026-10-05"
EOL = FIXTURES / "endoflife" / "coleta_2026-10-06"
NVD = FIXTURES / "nvd" / "coleta_2026-10-06"
PROCESSED = RAIZ / "dataset" / "processed"
SAIDAS = [
    normalizar.HARDWARE_CSV,
    normalizar.SOFTWARE_CSV,
    normalizar.PRODUTOS_CSV,
    normalizar.LEIAME,
]


@pytest.fixture(autouse=True)
def _sem_rede(monkeypatch):
    def recusar(*_a, **_k):
        raise AssertionError("o ETL não pode usar a rede")

    monkeypatch.setattr(socket.socket, "connect", recusar)


def _csv(caminho: Path) -> list[dict[str, str]]:
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


@pytest.fixture(scope="module")
def saida(tmp_path_factory) -> Path:
    pasta = tmp_path_factory.mktemp("processed")
    normalizar.gerar(COMPRAS, EOL, NVD, pasta)
    return pasta


# ---- ponta a ponta com as coletas reais -----------------------------------------------------


def test_gera_os_quatro_arquivos_a_partir_das_fixtures_sem_rede(saida):
    assert sorted(p.name for p in saida.iterdir()) == sorted(SAIDAS)


def test_duas_execucoes_produzem_saida_identica_byte_a_byte(saida, tmp_path):
    normalizar.gerar(COMPRAS, EOL, NVD, tmp_path)

    for nome in SAIDAS:
        assert (tmp_path / nome).read_bytes() == (saida / nome).read_bytes(), nome


def test_o_que_esta_versionado_em_dataset_processed_e_exatamente_o_que_as_fixtures_geram(saida):
    for nome in SAIDAS:
        assert (PROCESSED / nome).read_bytes() == (saida / nome).read_bytes(), nome
    assert sorted(p.name for p in PROCESSED.iterdir() if p.name != ".gitkeep") == sorted(SAIDAS)


def test_a_saida_nao_depende_do_dia_em_que_o_script_roda(tmp_path, monkeypatch):
    class Dia20300101(date):
        @classmethod
        def today(cls):
            return date(2030, 1, 1)

    monkeypatch.setattr(normalizar, "date", Dia20300101)
    normalizar.gerar(COMPRAS, EOL, NVD, tmp_path)

    for nome in SAIDAS:
        assert (tmp_path / nome).read_bytes() == (PROCESSED / nome).read_bytes(), nome


# ---- hardware -------------------------------------------------------------------------------


def test_hardware_e_o_conjunto_elegivel_do_exportador_classificado_pelas_regras_existentes(saida):
    linhas = _csv(saida / normalizar.HARDWARE_CSV)
    filtrado = exportador.filtrar(exportador.ler_registros(COMPRAS))

    assert len(linhas) == len(filtrado["elegiveis"]) == 467  # mesmo número do LEIAME de demo/
    assert {int(linha["pdm"]) for linha in linhas} == set(exportador.CATEGORIA_POR_PDM)
    for linha in linhas:
        assert linha["categoria"] == exportador.CATEGORIA_POR_PDM[int(linha["pdm"])]
    assert [linha["id_item_compra"] for linha in linhas] == sorted(
        (linha["id_item_compra"] for linha in linhas), key=int
    )
    por_id = {str(r["idItemCompra"]): r for r in filtrado["elegiveis"]}
    for linha in linhas:
        registro = por_id[linha["id_item_compra"]]
        assert linha["nome"] == exportador.nome_do_ativo(registro)
        assert linha["preco_unitario"] == str(exportador.arredondar(registro["precoUnitario"]))
        assert linha["fornecedor_cnpj"] == registro["niFornecedor"]


def test_hardware_nao_leva_pessoa_fisica_nem_numero_de_onze_digitos(saida):
    texto = (saida / normalizar.HARDWARE_CSV).read_text(encoding="utf-8")

    assert not re.search(r"(?<!\d)\d{11}(?!\d)", texto)
    assert "fornecedor_razao_social" not in _csv(saida / normalizar.HARDWARE_CSV)[0]  # só o CNPJ
    filtrado = exportador.filtrar(exportador.ler_registros(COMPRAS))
    pessoas = {
        r["niFornecedor"]
        for r in filtrado["federais"]
        if exportador.razao_de_pessoa_fisica(exportador._razao(r))
    }
    cnpjs = {linha["fornecedor_cnpj"] for linha in _csv(saida / normalizar.HARDWARE_CSV)}
    assert pessoas and not (pessoas & cnpjs)  # nenhum CNPJ de pessoa física passou


def test_pdm_sem_categoria_e_erro_explicito_e_nao_linha_sem_classificar(tmp_path):
    pasta = tmp_path / "compras_gov" / "2026-10-05"
    pasta.mkdir(parents=True)
    registro = {
        "esfera": "F",
        "niFornecedor": "11111111000111",
        "nomeFornecedor": "ALFA LTDA",
        "idCompra": 1,
        "idCompraItem": "1-1",
        "idItemCompra": 1,
        "codigoPdm": "999999",
        "nomePdm": "OUTRO",
        "marca": "X",
        "precoUnitario": 10.0,
        "dataCompra": "2026-01-10",
    }
    (pasta / "codigoPdm_999999_p001.json").write_text(json.dumps({"resultado": [registro]}))

    with pytest.raises(ErroNormalizacao, match="PDM 999999 sem categoria"):
        normalizar.hardware(pasta)


# ---- situação na data da coleta -------------------------------------------------------------


@pytest.mark.parametrize(
    ("eol", "esperado"),
    [
        ("2026-10-05", "FORA_DE_SUPORTE"),  # já passou
        ("2026-10-06", "FORA_DE_SUPORTE"),  # o dia do fim de suporte já é de fim
        ("2026-10-07", "EM_SUPORTE"),
        (False, "SEM_DATA_DE_FIM"),
        (True, "FORA_DE_SUPORTE"),
    ],
)
def test_situacao_na_data_da_coleta(eol, esperado):
    assert normalizar.situacao(eol, date(2026, 10, 6)) == esperado


@pytest.mark.parametrize("eol", ["amanhã", "2026-13-40", None, 5, ""])
def test_situacao_com_valor_que_a_fonte_nao_usa_e_erro_explicito(eol):
    with pytest.raises(ErroNormalizacao, match="eol"):
        normalizar.situacao(eol, date(2026, 10, 6))


def test_a_situacao_usa_a_data_da_pasta_de_origem_nao_a_do_arquivo_nem_a_de_hoje(tmp_path):
    """Office 2021 acaba em 2026-10-13: em suporte em 2026-10-06, fora em 2026-10-14."""
    mesma_coleta = tmp_path / "endoflife" / "2026-10-14"
    shutil.copytree(EOL, mesma_coleta)

    normalizar.gerar(COMPRAS, mesma_coleta, NVD, tmp_path / "saida")

    por_versao = {
        (r["produto"], r["versao"]): r for r in _csv(tmp_path / "saida" / normalizar.SOFTWARE_CSV)
    }
    assert por_versao[("office", "2021")]["data_coleta_endoflife"] == "2026-10-14"
    assert por_versao[("office", "2021")]["situacao_na_coleta"] == "FORA_DE_SUPORTE"
    original = {(r["produto"], r["versao"]): r for r in _csv(PROCESSED / normalizar.SOFTWARE_CSV)}
    assert original[("office", "2021")]["situacao_na_coleta"] == "EM_SUPORTE"


# ---- software: cruzamento conservador -------------------------------------------------------


def test_software_tem_uma_linha_por_ciclo_do_endoflife_com_data_de_fim_e_situacao(saida):
    linhas = _csv(saida / normalizar.SOFTWARE_CSV)
    esperados = {
        produto: json.loads((EOL / f"{produto}.json").read_text())
        for produto in endoflife_produtos()
    }

    for produto, ciclos in esperados.items():
        do_produto = [linha for linha in linhas if linha["produto"] == produto]
        assert sorted(linha["versao"] for linha in do_produto) == sorted(c["cycle"] for c in ciclos)
        for ciclo in ciclos:
            linha = next(x for x in do_produto if x["versao"] == ciclo["cycle"])
            assert linha["data_lancamento"] == ciclo["releaseDate"]
            assert linha["data_fim_suporte"] == (ciclo["eol"] if ciclo["eol"] else "")
            assert linha["data_coleta_endoflife"] == "2026-10-06"


def endoflife_produtos() -> list[str]:
    return endoflife.carregar_configuracao().produtos


def test_cve_por_severidade_vem_das_respostas_do_nvd_e_o_resto_e_sem_cvss_v3(saida):
    linhas = {(r["produto"], r["versao"]): r for r in _csv(saida / normalizar.SOFTWARE_CSV)}
    cruzadas = [r for r in linhas.values() if r["cruzamento_nvd"] == "CRUZADO"]

    assert len(cruzadas) == 14  # 7 produtos x 2 ciclos consultados
    for linha in cruzadas:
        nome = f"{linha['produto']}_{linha['versao']}"
        total = json.loads((NVD / f"{nome}_total.json").read_text())["totalResults"]
        por_severidade = {
            sev: json.loads((NVD / f"{nome}_{sev}.json").read_text())["totalResults"]
            for sev in nvd.SEVERIDADES
        }
        assert int(linha["cves_baixa"]) == por_severidade["LOW"]
        assert int(linha["cves_media"]) == por_severidade["MEDIUM"]
        assert int(linha["cves_alta"]) == por_severidade["HIGH"]
        assert int(linha["cves_critica"]) == por_severidade["CRITICAL"]
        assert int(linha["cves_total"]) == total
        assert int(linha["cves_sem_cvss_v3"]) == total - sum(por_severidade.values())
        assert linha["motivo_nao_cruzado"] == ""


def test_software_nao_cruzado_fica_explicito_sem_cve_inventada(saida):
    linhas = _csv(saida / normalizar.SOFTWARE_CSV)
    nao = [r for r in linhas if r["cruzamento_nvd"] == "NAO_CRUZADO"]

    assert nao and len(nao) == len(linhas) - 14
    for linha in nao:
        assert linha["motivo_nao_cruzado"]
        for coluna in (
            "cves_baixa",
            "cves_media",
            "cves_alta",
            "cves_critica",
            "cves_sem_cvss_v3",
            "cves_total",
        ):
            assert linha[coluna] == ""  # vazio, nunca 0: zero seria uma contagem que não houve
    office = {r["motivo_nao_cruzado"] for r in nao if r["produto"] == "office"}
    assert office == {"NVD: produto sem CPE configurado em collectors/config.yaml"}
    fora_da_lista = {r["motivo_nao_cruzado"] for r in nao if r["produto"] == "postgresql"}
    assert fora_da_lista == {"NVD: ciclo fora da lista consultada em collectors/config.yaml"}


def test_o_cruzamento_nao_aproxima_nomes_parecidos(tmp_path):
    """`postgres` não é `postgresql` e o ciclo `1.3` não é `1.30`: só igualdade exata."""
    eol = _eol(tmp_path, {"postgresql": [("16", "2028-11-09"), ("1.30", False)]})
    nvd_dir = _nvd(tmp_path, {("postgres", "16"): (1, 0, 0, 0, 1)})
    cfg_eol = _cfg_eol(["postgresql"])
    cfg_nvd = _cfg_nvd({"postgres": ["16"]})

    resultado = normalizar.software(eol, nvd_dir, cfg_eol, cfg_nvd)

    por_produto = {p["produto"]: p for p in resultado["produtos"]}
    assert por_produto["postgresql"]["no_nvd"] == "NAO"
    assert por_produto["postgres"]["no_endoflife"] == "NAO"
    assert por_produto["postgres"]["cruzado"] == "NAO"
    assert all(linha["cruzamento_nvd"] == "NAO_CRUZADO" for linha in resultado["linhas"])


def test_ciclo_do_nvd_que_nao_existe_no_endoflife_e_erro_de_configuracao(tmp_path):
    eol = _eol(tmp_path, {"alfa": [("2", "2030-01-01")]})
    nvd_dir = _nvd(tmp_path, {("alfa", "1"): (0, 0, 0, 0, 0)})

    with pytest.raises(ErroNormalizacao, match="alfa.*1.*não existe no endoflife"):
        normalizar.software(eol, nvd_dir, _cfg_eol(["alfa"]), _cfg_nvd({"alfa": ["1"]}))


def test_coleta_incompleta_do_nvd_deixa_o_produto_nao_cruzado_com_o_motivo(tmp_path):
    eol = _eol(tmp_path, {"alfa": [("1", "2030-01-01"), ("2", "2031-01-01")]})
    nvd_dir = _nvd(tmp_path, {("alfa", "1"): (0, 1, 0, 0, 1)})  # falta o ciclo 2

    resultado = normalizar.software(
        eol, nvd_dir, _cfg_eol(["alfa"]), _cfg_nvd({"alfa": ["1", "2"]})
    )

    produto = resultado["produtos"][0]
    assert (produto["no_endoflife"], produto["no_nvd"], produto["cruzado"]) == ("SIM", "NAO", "NAO")
    assert produto["motivo"] == "NVD: coleta ausente ou incompleta para o ciclo 2"
    assert {r["cruzamento_nvd"] for r in resultado["linhas"]} == {"NAO_CRUZADO"}


def test_produto_sem_coleta_no_endoflife_nao_vira_linha_de_software(tmp_path):
    eol = _eol(tmp_path, {})
    nvd_dir = _nvd(tmp_path, {})

    resultado = normalizar.software(eol, nvd_dir, _cfg_eol(["alfa"]), _cfg_nvd({}))

    assert resultado["linhas"] == []
    assert (
        resultado["produtos"][0]["motivo"]
        == f"{normalizar.MOTIVO_SEM_ENDOFLIFE}; {normalizar.MOTIVO_SEM_CPE}"
    )


def test_contagens_do_nvd_incoerentes_sao_erro_explicito(tmp_path):
    eol = _eol(tmp_path, {"alfa": [("1", "2030-01-01")]})
    nvd_dir = _nvd(tmp_path, {("alfa", "1"): (5, 5, 5, 5, 3)})  # 20 por severidade, total 3

    with pytest.raises(ErroNormalizacao, match="alfa.*1.*soma das severidades"):
        normalizar.software(eol, nvd_dir, _cfg_eol(["alfa"]), _cfg_nvd({"alfa": ["1"]}))


# ---- a contagem do D.6 ----------------------------------------------------------------------


def test_contagem_do_d6_confere_com_os_arquivos_das_fixtures(saida):
    produtos = _csv(saida / normalizar.PRODUTOS_CSV)
    eol_arquivos = {p.stem for p in EOL.glob("*.json")}
    nvd_produtos = {p.name.rsplit("_", 2)[0] for p in NVD.glob("*_total.json")}

    assert len(produtos) == len(eol_arquivos | nvd_produtos) == 8
    assert {p["produto"] for p in produtos if p["no_endoflife"] == "SIM"} == eol_arquivos
    assert {p["produto"] for p in produtos if p["no_nvd"] == "SIM"} == nvd_produtos
    ambas = {p["produto"] for p in produtos if p["cruzado"] == "SIM"}
    assert ambas == eol_arquivos & nvd_produtos
    nao = [p for p in produtos if p["cruzado"] == "NAO"]
    assert [(p["produto"], p["motivo"]) for p in nao] == [
        ("office", "NVD: produto sem CPE configurado em collectors/config.yaml")
    ]


def test_o_leiame_traz_a_mesma_contagem_dos_arquivos(saida):
    produtos = _csv(saida / normalizar.PRODUTOS_CSV)
    software = _csv(saida / normalizar.SOFTWARE_CSV)
    hardware = _csv(saida / normalizar.HARDWARE_CSV)
    texto = (saida / normalizar.LEIAME).read_text(encoding="utf-8")

    def numero(rotulo: str) -> int:
        achado = re.search(rf"\| {re.escape(rotulo)} \| \*\*(\d+)\*\* \|", texto)
        assert achado, rotulo
        return int(achado.group(1))

    assert numero("Produtos analisados") == len(produtos)
    assert numero("Com correspondência no endoflife") == sum(
        p["no_endoflife"] == "SIM" for p in produtos
    )
    assert numero("Com correspondência no NVD") == sum(p["no_nvd"] == "SIM" for p in produtos)
    assert numero("Com correspondência nas duas fontes") == sum(
        p["cruzado"] == "SIM" for p in produtos
    )
    assert numero("Não cruzados") == sum(p["cruzado"] == "NAO" for p in produtos)
    assert numero("Versões (ciclos) do endoflife") == len(software)
    assert numero("Versões cruzadas com o NVD") == sum(
        r["cruzamento_nvd"] == "CRUZADO" for r in software
    )
    assert numero("Registros de hardware normalizados") == len(hardware)
    for p in produtos:
        if p["cruzado"] == "NAO":
            assert f"| {p['produto']} | {p['motivo']} |" in texto


def test_o_leiame_declara_fontes_limitacoes_e_o_que_nao_vai_ao_banco(saida):
    texto = (saida / normalizar.LEIAME).read_text(encoding="utf-8")

    for trecho in (
        "https://dadosabertos.compras.gov.br",
        "https://endoflife.date",
        "https://services.nvd.nist.gov",
        "2026-10-05",
        "2026-10-06",
        "endoflife e NVD não são carregados no banco, não aparecem nas telas do ITAM e não geram "
        "alertas na versão atual.",
        "Só o dataset do Compras.gov.br usado na demonstração",
        "## Limitações",
        "## Metodologia",
    ):
        assert trecho in texto, trecho
    for produto in endoflife_produtos():
        assert f"`{produto}`" in texto


def test_o_leiame_diz_que_cpe_e_faixas_sao_manuais_e_que_so_14_ciclos_foram_consultados(saida):
    texto = (saida / normalizar.LEIAME).read_text(encoding="utf-8")
    consultados = sum(len(p.ciclos) for p in nvd.carregar_configuracao().produtos)

    assert consultados == 14
    for trecho in (
        "O identificador de cada produto no NVD (o CPE) e a faixa de versão de cada ciclo foram "
        "**definidos manualmente** em `python/collectors/config.yaml`",
        f"Só os **{consultados} ciclos** da tabela acima foram consultados no NVD.",
        "As demais versões ficaram fora **por decisão** de limitar o volume, não por falha de "
        "correspondência",
    ):
        assert trecho in texto, trecho


def test_o_leiame_explica_que_contagem_zero_nao_e_ausencia_de_vulnerabilidade(saida):
    texto = (saida / normalizar.LEIAME).read_text(encoding="utf-8")
    zeros = sorted(
        f"{r['produto']} {r['versao']}"
        for r in _csv(saida / normalizar.SOFTWARE_CSV)
        if r["cves_total"] == "0"
    )

    assert zeros == ["nginx 1.28", "nginx 1.30"]  # o que as fixtures reais mostram
    assert (
        "Contagem **zero** significa **nenhuma CVE encontrada por esta consulta**, não ausência "
        "de vulnerabilidades" in texto
    )
    assert "Na coleta de 2026-10-06, tiveram contagem zero: `nginx` 1.30 e `nginx` 1.28." in texto
    assert "tests/fixtures/nvd/ORIGEM.md" in texto  # a conferência com o CPE antigo do nginx


def test_sem_nenhum_ciclo_com_contagem_zero_o_leiame_nao_cita_zero_nenhum(tmp_path):
    eol = _eol(tmp_path, {"alfa": [("1", "2030-01-01")]})
    nvd_dir = _nvd(tmp_path, {("alfa", "1"): (0, 1, 0, 0, 1)})

    normalizar.gerar(
        COMPRAS, eol, nvd_dir, tmp_path / "s", _cfg_eol(["alfa"]), _cfg_nvd({"alfa": ["1"]})
    )

    texto = (tmp_path / "s" / normalizar.LEIAME).read_text(encoding="utf-8")
    assert "tiveram contagem zero" not in texto
    assert "Contagem **zero** significa" in texto  # a regra de leitura vale sempre


def test_zero_de_outro_produto_e_citado_sem_a_nota_do_nginx(tmp_path):
    eol = _eol(tmp_path, {"alfa": [("1", "2030-01-01")]})
    nvd_dir = _nvd(tmp_path, {("alfa", "1"): (0, 0, 0, 0, 0)})

    normalizar.gerar(
        COMPRAS, eol, nvd_dir, tmp_path / "s", _cfg_eol(["alfa"]), _cfg_nvd({"alfa": ["1"]})
    )

    texto = (tmp_path / "s" / normalizar.LEIAME).read_text(encoding="utf-8")
    assert "tiveram contagem zero: `alfa` 1." in texto
    assert "nginx" not in texto.split("### Como ler as contagens do NVD")[1].split("| Contagem")[0]


# ---- coleta mais recente, data e linha de comando -------------------------------------------


def test_a_data_da_coleta_e_a_da_pasta_e_pasta_sem_data_e_erro():
    assert normalizar.data_da_coleta(Path("dataset/raw/nvd/2026-10-06")) == date(2026, 10, 6)
    with pytest.raises(ErroNormalizacao, match="data"):
        normalizar.data_da_coleta(Path("dataset/raw/nvd/ontem"))


def test_main_gera_na_pasta_pedida_e_sai_com_0(tmp_path, capsys):
    codigo = normalizar.main(
        [
            "--compras", str(COMPRAS),
            "--endoflife", str(EOL),
            "--nvd", str(NVD),
            "--saida", str(tmp_path),
        ]
    )  # fmt: skip

    assert codigo == 0
    assert (tmp_path / normalizar.LEIAME).exists()
    assert "467 registros de hardware" in capsys.readouterr().out


def test_main_sem_coleta_sai_com_1_e_mostra_o_motivo(tmp_path, capsys):
    codigo = normalizar.main(
        [
            "--compras", str(tmp_path / "vazia"),
            "--endoflife", str(EOL),
            "--nvd", str(NVD),
            "--saida", str(tmp_path / "s"),
        ]
    )  # fmt: skip

    assert codigo == 1
    assert "Normalização recusada" in capsys.readouterr().err
    assert not (tmp_path / "s").exists()


# ---- ajudantes para os casos de borda -------------------------------------------------------


def _cfg_eol(produtos: list[str]) -> endoflife.Configuracao:
    return endoflife.Configuracao(
        base_url="https://endoflife.date", endpoint="/api/{produto}.json", produtos=produtos
    )


def _cfg_nvd(produtos: dict[str, list[str]]) -> nvd.Configuracao:
    ciclos = {
        produto: [Ciclo(c, "cpe:2.3:a:x:y", "1.0", "2.0") for c in versoes]
        for produto, versoes in produtos.items()
    }
    return nvd.Configuracao(
        base_url="https://services.nvd.nist.gov",
        endpoint="/rest/json/cves/2.0",
        produtos=[Produto(p, c) for p, c in ciclos.items()]
        or [Produto("x", [Ciclo("1", "cpe:2.3:a:x:y")])],
    )


def _eol(base: Path, produtos: dict[str, list[tuple[str, object]]]) -> Path:
    pasta = base / "endoflife" / "2026-10-06"
    pasta.mkdir(parents=True)
    for produto, ciclos in produtos.items():
        corpo = [{"cycle": c, "releaseDate": "2020-01-01", "eol": eol} for c, eol in ciclos]
        (pasta / f"{produto}.json").write_text(json.dumps(corpo))
    return pasta


def _nvd(base: Path, ciclos: dict[tuple[str, str], tuple[int, int, int, int, int]]) -> Path:
    """`(baixa, media, alta, critica, total)` por (produto, ciclo)."""
    pasta = base / "nvd" / "2026-10-06"
    pasta.mkdir(parents=True)
    for (produto, ciclo), contagens in ciclos.items():
        for sufixo, total in zip((*nvd.SEVERIDADES, "total"), contagens, strict=True):
            corpo = {"resultsPerPage": 1, "totalResults": total, "vulnerabilities": []}
            (pasta / f"{produto}_{ciclo}_{sufixo}.json").write_text(json.dumps(corpo))
    return pasta
