"""Recusa de `SECRET_KEY` padrão fora do ambiente local (docs/spec/configuracao.md §13.1).

`get_settings` é cacheada e o `conftest.py` já a carregou: cada teste esvazia o cache antes e
depois, em `monkeypatch`, para não herdar nem deixar configuração. O cwd vai para um diretório
vazio porque `Settings` lê o `.env` do diretório corrente.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.config import (
    SECRET_KEY_PADRAO,
    ConfiguracaoInvalidaError,
    Settings,
    get_settings,
    validar_configuracao,
)

RAIZ_PYTHON = Path(__file__).resolve().parents[2]
CHAVE_PROPRIA = "chave-propria-de-teste-Zx9-longa-o-bastante-0123456789"


@pytest.fixture(autouse=True)
def _ambiente_isolado(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _config(monkeypatch, ambiente, chave=None):
    monkeypatch.setenv("ENVIRONMENT", ambiente)
    if chave is not None:
        monkeypatch.setenv("SECRET_KEY", chave)
    get_settings.cache_clear()
    return get_settings()


def test_chave_padrao_em_ambiente_local_inicia(monkeypatch):
    configuracao = _config(monkeypatch, "local")

    assert configuracao.secret_key == SECRET_KEY_PADRAO


def test_sem_environment_o_padrao_e_local_e_inicia():
    assert get_settings().environment == "local"


@pytest.mark.parametrize("ambiente", ["docker", "producao", "homologacao", "Docker", " docker "])
def test_chave_padrao_fora_do_local_recusa(monkeypatch, ambiente):
    with pytest.raises(ConfiguracaoInvalidaError) as erro:
        _config(monkeypatch, ambiente)

    mensagem = str(erro.value)
    assert "SECRET_KEY" in mensagem
    assert "secrets.token_urlsafe" in mensagem  # diz o que fazer
    assert "ENVIRONMENT=local" in mensagem
    assert SECRET_KEY_PADRAO not in mensagem  # nunca mostra a chave


@pytest.mark.parametrize(
    "chave", ["", "   ", "troque-esta-chave", "troque-esta-chave-em-qualquer-ambiente-real"]
)
def test_chaves_de_exemplo_e_vazia_tambem_recusam_fora_do_local(monkeypatch, chave):
    with pytest.raises(ConfiguracaoInvalidaError) as erro:
        _config(monkeypatch, "docker", chave)

    assert "troque-esta-chave" not in str(erro.value)


def test_chave_propria_fora_do_local_inicia(monkeypatch):
    configuracao = _config(monkeypatch, "docker", CHAVE_PROPRIA)

    assert configuracao.environment == "docker"
    assert configuracao.secret_key == CHAVE_PROPRIA


def test_mensagem_de_recusa_nao_vaza_a_chave_recebida():
    # Uma chave de exemplo com outro texto na lista de recusadas não pode aparecer na mensagem;
    # e o erro é o próprio, não um erro de validação do Pydantic (que traria o valor de entrada).
    configuracao = Settings(environment="producao", secret_key="")
    with pytest.raises(ConfiguracaoInvalidaError) as erro:
        validar_configuracao(configuracao)

    assert not hasattr(erro.value, "errors")
    assert "input" not in str(erro.value).lower()


def test_recusa_nao_fica_no_cache(monkeypatch):
    with pytest.raises(ConfiguracaoInvalidaError):
        _config(monkeypatch, "docker")

    monkeypatch.setenv("SECRET_KEY", CHAVE_PROPRIA)  # sem limpar o cache à mão

    assert get_settings().secret_key == CHAVE_PROPRIA


def _iniciar_aplicacao(cwd, ambiente, chave=None):
    """Importa `app.main` num processo novo, como o `uvicorn` faz ao iniciar."""
    ambiente_do_processo = {
        k: v
        for k, v in os.environ.items()
        if k not in ("ENVIRONMENT", "SECRET_KEY", "DATABASE_URL")
    }
    ambiente_do_processo.update(ENVIRONMENT=ambiente, PYTHONPATH=str(RAIZ_PYTHON))
    if chave is not None:
        ambiente_do_processo["SECRET_KEY"] = chave
    return subprocess.run(  # noqa: S603  # nosec B603
        [sys.executable, "-c", "import app.main"],
        env=ambiente_do_processo,
        cwd=cwd,  # diretório vazio: o `.env` real da raiz do repositório não pode interferir
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_aplicacao_com_chave_padrao_e_environment_docker_se_recusa_a_iniciar(tmp_path):
    resultado = _iniciar_aplicacao(tmp_path, "docker")

    assert resultado.returncode != 0
    assert "ConfiguracaoInvalidaError" in resultado.stderr
    assert "SECRET_KEY padrão ou vazia não é aceita com ENVIRONMENT='docker'" in resultado.stderr
    assert SECRET_KEY_PADRAO not in resultado.stderr


def test_aplicacao_com_chave_padrao_em_local_inicia(tmp_path):
    assert _iniciar_aplicacao(tmp_path, "local").returncode == 0


def test_aplicacao_com_chave_propria_em_docker_inicia(tmp_path):
    resultado = _iniciar_aplicacao(tmp_path, "docker", CHAVE_PROPRIA)

    assert resultado.returncode == 0, resultado.stderr
    assert CHAVE_PROPRIA not in resultado.stderr
