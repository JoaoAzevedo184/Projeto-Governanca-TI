"""Coletas de referência: os arquivos versionados de `dataset/demo/` e `dataset/processed/` são o
retrato das coletas fixadas em `collectors/config.yaml` (bloco `referencia`), e uma coleta mais
recente em `dataset/raw/` não os altera. Usar outra coleta exige parâmetro explícito e uma saída
que não seja o diretório versionado. Sem rede.
"""

import re
import shutil
import socket
import sys
from pathlib import Path

import pytest

from etl import exportar_inventario_demo as exportador
from etl import normalizar, paths
from etl.paths import ErroReferencia

RAIZ = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
FONTES = ("compras_gov", "endoflife", "nvd")
FIXTURE_DE = {"compras_gov": "compras_gov", "endoflife": "endoflife", "nvd": "nvd"}
DEMO = RAIZ / "dataset" / "demo"
PROCESSED = RAIZ / "dataset" / "processed"
ARQUIVOS_PROCESSED = [normalizar.HARDWARE_CSV, normalizar.SOFTWARE_CSV, normalizar.PRODUTOS_CSV]
ARQUIVOS_DEMO = ["inventario_demo.csv", "fornecedores_demo.csv", "inventario_demo.LEIAME.md"]


@pytest.fixture(autouse=True)
def _sem_rede(monkeypatch):
    def recusar(*_a, **_k):
        raise AssertionError("sem rede")

    monkeypatch.setattr(socket.socket, "connect", recusar)


def _fixture(fonte: str) -> Path:
    return FIXTURES / FIXTURE_DE[fonte] / f"coleta_{paths.coleta_de_referencia(fonte)}"


@pytest.fixture
def raw(tmp_path, monkeypatch) -> Path:
    """Um `dataset/` descartável com as coletas de referência (cópia das fixtures reais) e, ao lado
    de cada uma, uma coleta MAIS RECENTE com dados diferentes."""
    base = tmp_path / "dataset"
    for fonte in FONTES:
        referencia = base / "raw" / fonte / paths.coleta_de_referencia(fonte)
        shutil.copytree(_fixture(fonte), referencia)
        nova = base / "raw" / fonte / "2099-01-01"
        shutil.copytree(referencia, nova)
        for arquivo in sorted(nova.glob("*.json"))[:3]:
            arquivo.unlink()  # a coleta nova é diferente da de referência
    monkeypatch.setattr(normalizar, "DATASET_DIR", base)
    monkeypatch.setattr(exportador, "DATASET_DIR", base)
    return base


# ---- a referência está fixada na configuração -----------------------------------------------


def test_a_configuracao_fixa_a_data_de_cada_fonte_e_as_fixtures_dessas_datas_existem():
    assert {f: paths.coleta_de_referencia(f) for f in FONTES} == {
        "compras_gov": "2026-10-05",
        "endoflife": "2026-10-06",
        "nvd": "2026-10-06",
    }
    for fonte in FONTES:
        assert _fixture(fonte).is_dir() and list(_fixture(fonte).glob("*.json")), fonte


def test_referencia_ausente_ou_invalida_na_configuracao_e_erro_explicito(tmp_path):
    sem_bloco = tmp_path / "a.yaml"
    sem_bloco.write_text("compras_gov: {}\n")
    sem_fonte = tmp_path / "b.yaml"
    sem_fonte.write_text('referencia:\n  nvd: "2026-10-06"\n')
    data_ruim = tmp_path / "c.yaml"
    data_ruim.write_text('referencia:\n  nvd: "ontem"\n')

    for arquivo, fonte in ((sem_bloco, "nvd"), (sem_fonte, "compras_gov"), (data_ruim, "nvd")):
        with pytest.raises(ErroReferencia, match=fonte):
            paths.coleta_de_referencia(fonte, arquivo)


def test_a_referencia_aceita_a_data_como_texto_ou_como_data_do_yaml(tmp_path):
    arquivo = tmp_path / "d.yaml"
    arquivo.write_text("referencia:\n  nvd: 2026-10-06\n")  # o YAML lê como data

    assert paths.coleta_de_referencia("nvd", arquivo) == "2026-10-06"


# ---- regras do destino ----------------------------------------------------------------------


@pytest.fixture
def versionado(tmp_path) -> Path:
    pasta = tmp_path / "versionado"
    pasta.mkdir()
    return pasta


def test_sem_coleta_informada_a_saida_padrao_e_a_versionada(versionado):
    assert paths.escolher_saida({}, None, versionado) == versionado


def test_coleta_informada_exige_saida_explicita(versionado):
    with pytest.raises(ErroReferencia, match="--saida"):
        paths.escolher_saida({"nvd": Path("raw/nvd/2099-01-01")}, None, versionado)


def test_ate_a_coleta_de_referencia_informada_exige_saida_explicita(versionado):
    """Informar a coleta é escolher: a saída tem de ser dita, mesmo com a data de referência."""
    with pytest.raises(ErroReferencia, match="exige informar --saida"):
        paths.escolher_saida({"nvd": Path("fixtures/coleta_2026-10-06")}, None, versionado)


def test_data_do_nome_so_aceita_data_de_calendario():
    assert paths.data_do_nome("coleta_2026-10-05") == "2026-10-05"
    assert paths.data_do_nome("2026-10-06") == "2026-10-06"
    assert paths.data_do_nome("coleta_2026-13-45") is None
    assert paths.data_do_nome("sem-data") is None


def test_coleta_nova_nao_pode_ter_o_diretorio_versionado_como_saida(versionado, tmp_path):
    nova = {"nvd": Path("raw/nvd/2099-01-01")}

    with pytest.raises(ErroReferencia, match="não é a de referência"):
        paths.escolher_saida(nova, versionado, versionado)
    with pytest.raises(ErroReferencia, match="não é a de referência"):  # nem pelo outro caminho
        paths.escolher_saida(nova, tmp_path / "versionado" / ".." / "versionado", versionado)
    assert paths.escolher_saida(nova, tmp_path / "outra", versionado) == tmp_path / "outra"


def test_coleta_de_referencia_informada_pode_regenerar_o_versionado(versionado):
    copia = {"nvd": Path("qualquer/lugar/coleta_2026-10-06")}  # a mesma data: é a referência

    assert paths.escolher_saida(copia, versionado, versionado) == versionado


def test_pasta_sem_data_nunca_conta_como_referencia(versionado):
    with pytest.raises(ErroReferencia, match="não é a de referência"):
        paths.escolher_saida({"nvd": Path("raw/nvd/ontem")}, versionado, versionado)


# ---- normalizador: coleta mais recente não altera a saída padrão ----------------------------


def test_uma_coleta_mais_recente_em_raw_nao_altera_a_saida_padrao_do_normalizador(raw):
    codigo = normalizar.main([])

    assert codigo == 0
    for nome in ARQUIVOS_PROCESSED:  # saiu da coleta de referência, não da de 2099
        assert (raw / "processed" / nome).read_bytes() == (PROCESSED / nome).read_bytes(), nome


def test_o_normalizador_recusa_uma_coleta_nova_sem_saida_e_nao_grava_nada(raw, capsys):
    nova = raw / "raw" / "nvd" / "2099-01-01"

    codigo = normalizar.main(["--nvd", str(nova)])

    assert codigo == 1
    assert "--saida" in capsys.readouterr().err
    assert not (raw / "processed").exists()


def test_o_normalizador_recusa_uma_coleta_nova_com_o_versionado_como_saida(raw, capsys):
    nova = raw / "raw" / "nvd" / "2099-01-01"
    versionado = raw / "processed"

    codigo = normalizar.main(["--nvd", str(nova), "--saida", str(versionado)])

    assert codigo == 1
    assert "não é a de referência" in capsys.readouterr().err
    assert not versionado.exists()


def test_o_normalizador_grava_a_coleta_nova_no_diretorio_informado_e_so_la(raw, tmp_path):
    saida = tmp_path / "experimento"
    nova = raw / "raw" / "endoflife" / "2099-01-01"

    codigo = normalizar.main(["--endoflife", str(nova), "--saida", str(saida)])

    assert codigo == 0
    assert (saida / normalizar.LEIAME).exists()
    assert not (raw / "processed").exists()  # o diretório versionado não foi tocado
    assert "2099-01-01" in (saida / normalizar.LEIAME).read_text(encoding="utf-8")


def test_a_coleta_de_referencia_informada_pode_regenerar_o_diretorio_versionado(raw):
    codigo = normalizar.main(
        [
            "--compras",
            str(raw / "raw" / "compras_gov" / "2026-10-05"),
            "--saida",
            str(raw / "processed"),
        ]
    )

    assert codigo == 0
    for nome in ARQUIVOS_PROCESSED:
        assert (raw / "processed" / nome).read_bytes() == (PROCESSED / nome).read_bytes()


def test_sem_a_referencia_em_raw_o_normalizador_falha_com_a_mensagem_de_como_proceder(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(normalizar, "DATASET_DIR", tmp_path / "vazio")

    codigo = normalizar.main([])

    erro = capsys.readouterr().err
    assert codigo == 1
    assert "coleta de referência ausente" in erro and "--saida" in erro
    assert not (tmp_path / "vazio").exists()


def test_com_se_houver_referencia_a_falta_dela_e_um_aviso_e_nada_e_gravado(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(normalizar, "DATASET_DIR", tmp_path / "vazio")

    codigo = normalizar.main(["--se-houver-referencia"])

    saida = capsys.readouterr()
    assert codigo == 0
    assert "mantidos" in saida.out and "referência" in saida.out
    assert not (tmp_path / "vazio").exists()


def test_com_se_houver_referencia_e_ela_presente_o_normalizador_roda_normalmente(raw):
    assert normalizar.main(["--se-houver-referencia"]) == 0

    assert (raw / "processed" / normalizar.LEIAME).exists()


# ---- exportador de demonstração -------------------------------------------------------------


def test_uma_coleta_mais_recente_em_raw_nao_altera_a_saida_padrao_do_exportador(raw, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["x"])

    codigo = exportador.main()

    assert codigo == 0
    for nome in ARQUIVOS_DEMO:
        assert (raw / "demo" / nome).read_bytes() == (DEMO / nome).read_bytes(), nome


def test_o_exportador_recusa_outra_coleta_sem_saida_ou_com_o_diretorio_versionado(
    raw, monkeypatch, capsys
):
    nova = raw / "raw" / "compras_gov" / "2099-01-01"

    monkeypatch.setattr(sys, "argv", ["x", "--raw", str(nova)])
    sem_saida = exportador.main()
    monkeypatch.setattr(sys, "argv", ["x", "--raw", str(nova), "--saida", str(raw / "demo")])
    na_versionada = exportador.main()

    erros = capsys.readouterr().err
    assert (sem_saida, na_versionada) == (1, 1)
    assert "--saida" in erros and "não é a de referência" in erros
    assert not (raw / "demo").exists()


def test_o_exportador_grava_a_coleta_nova_so_no_diretorio_informado(raw, monkeypatch, tmp_path):
    nova = raw / "raw" / "compras_gov" / "2026-10-05"
    saida = tmp_path / "experimento"
    monkeypatch.setattr(sys, "argv", ["x", "--raw", str(nova), "--saida", str(saida)])

    assert exportador.main() == 0

    assert (saida / "inventario_demo.csv").exists() and not (raw / "demo").exists()


# ---- os LEIAME explicam o retrato -----------------------------------------------------------


@pytest.mark.parametrize(
    "arquivo",
    [DEMO / "inventario_demo.LEIAME.md", PROCESSED / "LEIAME.md"],
    ids=["demo", "processed"],
)
def test_os_leiame_dizem_que_os_arquivos_sao_um_retrato_e_que_a_fonte_muda(arquivo):
    texto = arquivo.read_text(encoding="utf-8")

    for trecho in (
        "## Reprodutibilidade: um retrato das coletas de referência",
        "14 dos 1705 registros",
        "uma coleta nova não reproduz estes arquivos",
        "exige parâmetro explícito",
        "docs/guia/coleta-de-dados.md",
    ):
        assert trecho in texto, trecho
    for fonte in FONTES:
        assert paths.coleta_de_referencia(fonte) in texto
    assert re.search(r"bloco `referencia` de `python/collectors/config.yaml`", texto)
