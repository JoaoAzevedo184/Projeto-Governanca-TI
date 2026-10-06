"""Guarda: as fixtures e os arquivos gerados dos coletores `endoflife` e `nvd` não trazem chave de
API, segredo nem dado pessoal.

Confere `tests/fixtures/{endoflife,nvd}/` e `dataset/processed/`: nada que pareça a `NVD_API_KEY`
(o valor real, se houver no `.env` ou no ambiente, nunca aparece em arquivo algum), cabeçalho
`apiKey`, CPF (formatado ou 11 dígitos soltos) ou e-mail fora da lista de caixas institucionais.
O teste mostra só o arquivo, nunca o valor encontrado.
"""

import os
import re
from pathlib import Path

import pytest

from etl.sanitizar_coleta import CPF_APOS_NOME

RAIZ = Path(__file__).resolve().parents[3]
FIXTURES = RAIZ / "python" / "tests" / "fixtures"
PASTAS = [FIXTURES / "endoflife", FIXTURES / "nvd", RAIZ / "dataset" / "processed"]
CPF_FORMATADO = re.compile(r"(?<!\d)\d{3}\.\d{3}\.\d{3}-\d{2}(?!\d)")
CPF_SOLTO = re.compile(r"(?<![0-9A-Za-z.\-/])\d{11}(?![0-9A-Za-z])")  # fora de hash e de id
CABECALHO = re.compile(r"(?i)api[-_ ]?key")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Caixas institucionais (segurança e listas de CNAs e fornecedores) que o NVD traz em
# `sourceIdentifier` e nas referências; conferidas em 2026-10-06 (`tests/fixtures/nvd/ORIGEM.md`).
# Outro endereço numa coleta nova exige revisão humana antes de ir ao git.
EMAILS_INSTITUCIONAIS = {
    "cna@mongodb.com",
    "cna@vuldb.com",
    "cybersecurity@se.com",
    "nvd@nist.gov",
    "package-announce@lists.fedoraproject.org",
    "secalert@redhat.com",
    "secalert_us@oracle.com",
    "secure@microsoft.com",
    "security-advisories@github.com",
    "security@apache.org",
    "security@opentext.com",
}


def _arquivos() -> list[Path]:
    achados = [
        p
        for pasta in PASTAS
        for p in sorted(pasta.rglob("*"))
        if p.suffix in {".json", ".csv"} or p.name == "LEIAME.md"  # os ORIGEM.md só explicam
    ]
    assert achados, "nenhum arquivo para conferir"
    return achados


def _chave_do_ambiente() -> str | None:
    chave = os.environ.get("NVD_API_KEY", "")
    env = RAIZ / ".env"
    if not chave and env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.startswith("NVD_API_KEY="):
                chave = linha.split("=", 1)[1]
    chave = chave.strip().strip("'\"")
    return chave if len(chave) >= 8 else None


def test_o_valor_real_da_nvd_api_key_nao_esta_em_nenhum_arquivo():
    chave = _chave_do_ambiente()
    if chave is None:
        pytest.skip("sem NVD_API_KEY no ambiente nem no .env: nada a procurar")

    com_a_chave = [str(a.relative_to(RAIZ)) for a in _arquivos() if chave in a.read_text("utf-8")]

    assert not com_a_chave, f"a chave aparece em: {com_a_chave}"


def test_nenhum_arquivo_tem_cabecalho_ou_nome_de_chave_de_api():
    com_chave = [
        str(a.relative_to(RAIZ)) for a in _arquivos() if CABECALHO.search(a.read_text("utf-8"))
    ]

    assert not com_chave, f"apiKey/NVD_API_KEY em: {com_chave}"


def test_nenhum_arquivo_tem_cpf():
    com_cpf = [
        str(a.relative_to(RAIZ))
        for a in _arquivos()
        if (texto := a.read_text("utf-8"))
        and (CPF_FORMATADO.search(texto) or CPF_SOLTO.search(texto) or CPF_APOS_NOME.search(texto))
    ]

    assert not com_cpf, f"número com cara de CPF em: {com_cpf}"


def test_so_ha_email_institucional_da_lista_fechada():
    fora_da_lista = sorted(
        {
            str(a.relative_to(RAIZ))
            for a in _arquivos()
            for email in EMAIL.findall(a.read_text("utf-8"))
            if email.lower() not in EMAILS_INSTITUCIONAIS
        }
    )

    assert not fora_da_lista, f"e-mail fora da lista institucional em: {fora_da_lista}"


def test_o_guarda_reconhece_o_que_procura():
    assert CABECALHO.search('{"apiKey": "x"}') and CABECALHO.search("NVD_API_KEY=x")
    assert CPF_FORMATADO.search("123.456.789-09") and CPF_SOLTO.search("12345678909")
    assert not CPF_SOLTO.search("web.archive.org/web/20211229071247/https")  # 14 dígitos
    assert EMAIL.search("pessoa@exemplo.com")
    assert "pessoa@exemplo.com" not in EMAILS_INSTITUCIONAIS
