"""Log estruturado (NFR-OBS-03): formato JSON e limpeza de dado sensível."""

import io
import json
import logging

import pytest

from app.core.logging import JsonFormatter, configurar_logging, limpar, request_id_ctx


def _registro(mensagem="evento", nivel=logging.INFO, exc_info=None, **extra):
    registro = logging.LogRecord("itam.teste", nivel, __file__, 1, mensagem, None, exc_info)
    for chave, valor in extra.items():
        setattr(registro, chave, valor)
    return registro


def test_formatador_emite_json_de_uma_linha_com_os_campos_do_spec():
    token = request_id_ctx.set("abc123")
    try:
        linha = JsonFormatter().format(_registro("olá", usuario_id=7, regra="BR-018"))
    finally:
        request_id_ctx.reset(token)

    evento = json.loads(linha)
    assert "\n" not in linha
    assert {"timestamp", "level", "logger", "mensagem", "request_id", "usuario_id", "regra"} <= set(
        evento
    )
    assert (evento["level"], evento["logger"], evento["mensagem"]) == ("INFO", "itam.teste", "olá")
    assert (evento["request_id"], evento["usuario_id"], evento["regra"]) == ("abc123", 7, "BR-018")
    assert evento["timestamp"].endswith("+00:00")


def test_formatador_sem_contexto_deixa_os_campos_nulos():
    evento = json.loads(JsonFormatter().format(_registro()))

    assert evento["request_id"] is None
    assert evento["usuario_id"] is None and evento["regra"] is None


def test_formatador_inclui_campos_da_requisicao_quando_existem():
    evento = json.loads(
        JsonFormatter().format(
            _registro(metodo="GET", caminho="/health", status=200, duracao_ms=1.5)
        )
    )

    assert (evento["metodo"], evento["caminho"], evento["status"]) == ("GET", "/health", 200)
    assert evento["duracao_ms"] == 1.5


def test_formatador_inclui_a_excecao_sem_vazar_parametros_de_sql():
    try:
        raise RuntimeError(
            "falhou [parameters: ('SENHA-HASH-AAAA-BBBB', 'CHAVE-REAL-1234-5678')] fim"
        )
    except RuntimeError:
        import sys

        linha = JsonFormatter().format(_registro("erro", logging.ERROR, exc_info=sys.exc_info()))

    assert "[parameters: ***]" in json.loads(linha)["excecao"]
    assert "SENHA-HASH" not in linha and "CHAVE-REAL" not in linha


@pytest.mark.parametrize(
    ("entrada", "proibido"),
    [
        ("chave ABCD-1234-EFGH-A3F9 ativa", "ABCD-1234"),
        ("Authorization: Bearer abc.def.ghi-123", "abc.def.ghi"),
        ("jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.assinatura_x ok", "eyJhbGci"),
        ("senha=minhasenha123 usuario=admin", "minhasenha123"),
        ('{"password": "segredo-forte", "login": "admin"}', "segredo-forte"),
        ("token: abcdef123456", "abcdef123456"),
        ("secret_key=troque-esta-chave", "troque-esta-chave"),
    ],
)
def test_limpar_mascara_dado_sensivel(entrada, proibido):
    assert proibido not in limpar(entrada)


def test_limpar_mascara_a_chave_no_padrao_do_sistema_e_preserva_o_sufixo():
    assert limpar("chave ABCD-1234-EFGH-A3F9") == "chave ****-****-A3F9"


@pytest.mark.parametrize(
    "texto",
    [
        "requisição concluída",
        "data 2026-03-20 e id 5f2c9d8e4b7a41c0a1b2c3d4e5f60718",
        "regra BR-018 aplicada ao ativo 12",
        "senha deve ter ao menos 8 caracteres",
    ],
)
def test_limpar_nao_estraga_texto_comum(texto):
    assert limpar(texto) == texto


def test_configurar_logging_e_idempotente_e_respeita_o_nivel():
    saida = io.StringIO()
    raiz = logging.getLogger()
    antes = list(raiz.handlers)
    nivel_antes = raiz.level
    try:
        configurar_logging("INFO", saida)
        configurar_logging("INFO", saida)
        instalados = [h for h in raiz.handlers if h not in antes]
        logging.getLogger("itam.teste").info("visível")
        logging.getLogger("itam.teste").debug("invisível")
    finally:
        for handler in [h for h in raiz.handlers if h not in antes]:
            raiz.removeHandler(handler)
        raiz.setLevel(nivel_antes)

    assert len(instalados) == 1
    linhas = saida.getvalue().splitlines()
    assert len(linhas) == 1 and json.loads(linhas[0])["mensagem"] == "visível"
