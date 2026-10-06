"""Guarda: nenhuma fixture versionada traz razão social seguida de 11 dígitos que não sejam zeros.

O formato antigo de microempreendedor individual é "NOME DA PESSOA" + CPF do titular. Fixtures
copiadas de uma coleta nova passam por `etl.sanitizar_coleta`. O teste mostra só o arquivo, nunca
o valor.
"""

import re
import subprocess
from pathlib import Path

from etl.sanitizar_coleta import CPF_APOS_NOME, ZEROS, sanitizar

RAIZ = Path(__file__).resolve().parents[2]
FIXTURES = RAIZ / "tests" / "fixtures"


def _versionados() -> list[Path]:
    saida = subprocess.run(
        ["git", "ls-files", "-z", "--", str(FIXTURES)],
        cwd=RAIZ,
        capture_output=True,
        check=True,
    ).stdout.decode()
    return [Path(p) for p in saida.split("\0") if p]


def test_nenhuma_fixture_versionada_tem_cpf_na_razao_social():
    arquivos = _versionados() or sorted(FIXTURES.rglob("*.json"))  # fora de um checkout git
    assert arquivos, "nenhuma fixture encontrada"
    com_cpf = [
        a.name
        for a in arquivos
        if a.suffix == ".json"
        and any(m.group(0) != ZEROS for m in CPF_APOS_NOME.finditer(a.read_text(encoding="utf-8")))
    ]
    assert not com_cpf, f"razão social com 11 dígitos diferentes de zeros em: {com_cpf}"


def test_a_sanitizacao_troca_so_os_onze_digitos_depois_do_nome():
    entrada = '{"nomeFornecedor": "FULANO DE TAL 12345678901", "niFornecedor": "12345678000199"}'
    assert sanitizar(entrada) == entrada.replace("12345678901", ZEROS)
    assert sanitizar(sanitizar(entrada)) == sanitizar(entrada)


def test_o_guarda_reconhece_um_cpf_que_nao_e_zero():
    assert re.search(CPF_APOS_NOME, "FULANO 98765432100")
    assert not re.search(CPF_APOS_NOME, '"niFornecedor": "12345678000199"')
