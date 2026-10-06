"""`scripts/collect.sh` roda os três coletores (compras_gov, endoflife e nvd) e a normalização."""

import importlib
import importlib.util
import re
import shutil
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
SCRIPT = RAIZ / "scripts" / "collect.sh"


def _modulos() -> list[str]:
    """Todo `python -m <modulo>` do script, na ordem."""
    return re.findall(r"^python -m ([\w.]+)(?: .*)?$", SCRIPT.read_text(), flags=re.MULTILINE)


def test_o_script_executa_os_tres_coletores_e_depois_a_normalizacao():
    assert _modulos() == [
        "collectors.compras_gov",
        "collectors.endoflife",
        "collectors.nvd",
        "etl.normalizar",
    ]


def test_cada_modulo_do_script_existe_e_tem_main():
    """`python -m etl` falhava: o pacote não tem `__main__`. O que o script chama tem de rodar."""
    for modulo in _modulos():
        especificacao = importlib.util.find_spec(modulo)
        assert especificacao is not None, modulo
        assert callable(importlib.import_module(modulo).main), modulo


def test_o_script_nao_carrega_o_env_nem_imprime_a_chave():
    texto = SCRIPT.read_text()

    assert ".env" not in texto and "NVD_API_KEY" not in texto


def _executar(tmp_path, ambiente: dict[str, str], com_python_falso: bool):
    """Roda o script com um PATH só com o que ele precisa; o `python` é um falso que anota o que
    recebeu, para o teste não coletar nada nem usar a rede."""
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    (bin_ / "dirname").symlink_to(shutil.which("dirname"))
    registro = tmp_path / "chamadas.txt"
    if com_python_falso:
        falso = bin_ / "python"
        falso.write_text(f'#!/bin/sh\necho "$@" >> {registro}\n')
        falso.chmod(0o755)
    resultado = subprocess.run(
        [shutil.which("bash"), str(SCRIPT)],
        env={"PATH": str(bin_), **ambiente},
        capture_output=True,
        text=True,
        check=False,
    )
    return resultado, registro


def test_sem_ambiente_virtual_o_script_falha_com_mensagem_clara_e_nao_coleta_nada(tmp_path):
    resultado, registro = _executar(tmp_path, {}, com_python_falso=True)

    assert resultado.returncode == 1
    assert "ambiente virtual" in resultado.stderr and "activate" in resultado.stderr
    assert "command not found" not in resultado.stderr and "não encontrado" not in resultado.stderr
    assert not registro.exists()  # nenhum coletor rodou


def test_com_ambiente_virtual_mas_sem_python_o_script_tambem_falha_com_mensagem_clara(tmp_path):
    resultado, _ = _executar(tmp_path, {"VIRTUAL_ENV": "/x"}, com_python_falso=False)

    assert resultado.returncode == 1
    assert "ambiente virtual" in resultado.stderr
    assert "command not found" not in resultado.stderr


def test_com_ambiente_virtual_roda_os_tres_coletores_e_a_normalizacao_da_referencia(tmp_path):
    resultado, registro = _executar(tmp_path, {"VIRTUAL_ENV": "/x"}, com_python_falso=True)

    assert resultado.returncode == 0, resultado.stderr
    assert registro.read_text().splitlines() == [
        "-m collectors.compras_gov",
        "-m collectors.endoflife",
        "-m collectors.nvd",
        "-m etl.normalizar --se-houver-referencia",  # só a referência: nunca a coleta de hoje
    ]
