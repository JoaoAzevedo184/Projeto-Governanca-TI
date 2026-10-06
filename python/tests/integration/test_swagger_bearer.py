"""Autenticação no Swagger: o esquema de segurança é HTTP Bearer (campo de token no Authorize).

Antes era `OAuth2PasswordBearer`: o botão Authorize enviava um formulário a `/auth/login`, que
espera JSON, e respondia 422. Aqui se confere o esquema no OpenAPI e que as respostas de erro de
autenticação seguem as mesmas, no formato de erro do projeto.
"""

import pytest

from app.main import app

METODOS = {"get", "post", "patch", "put", "delete"}


def _operacoes(openapi):
    for caminho, itens in openapi["paths"].items():
        for metodo, operacao in itens.items():
            if metodo in METODOS:
                yield caminho, metodo, operacao


def test_o_esquema_de_seguranca_e_http_bearer_sem_fluxo_oauth2(client):
    esquemas = client.get("/openapi.json").json()["components"]["securitySchemes"]

    assert list(esquemas) == ["HTTPBearer"]
    assert esquemas["HTTPBearer"]["type"] == "http"
    assert esquemas["HTTPBearer"]["scheme"] == "bearer"
    assert "flows" not in esquemas["HTTPBearer"]


def test_toda_rota_protegida_usa_o_bearer_e_o_login_segue_aberto(client):
    openapi = client.get("/openapi.json").json()

    protegidas = [(c, m) for c, m, op in _operacoes(openapi) if op.get("security")]
    assert len(protegidas) > 30
    for caminho, metodo, operacao in _operacoes(openapi):
        if operacao.get("security"):
            assert operacao["security"] == [{"HTTPBearer": []}], (caminho, metodo)
    login = openapi["paths"]["/api/v1/auth/login"]["post"]
    assert "security" not in login
    # o login continua recebendo JSON, não formulário
    assert list(login["requestBody"]["content"]) == ["application/json"]


def test_o_documento_do_openapi_versionado_e_o_da_aplicacao():
    from pathlib import Path

    import yaml

    versionado = yaml.safe_load(Path("api/openapi.yaml").read_text(encoding="utf-8"))

    assert (
        versionado["components"]["securitySchemes"]
        == app.openapi()["components"]["securitySchemes"]
    )


def test_a_pagina_do_swagger_carrega(client):
    resposta = client.get("/docs")

    assert resposta.status_code == 200 and "swagger-ui" in resposta.text.lower()


@pytest.mark.parametrize(
    ("cabecalho", "tipo", "detalhe", "www_authenticate"),
    [
        (None, "/erros/http-401", "Not authenticated", True),
        ("Basic abc", "/erros/http-401", "Not authenticated", True),
        ("Bearer ", "/erros/nao-autenticado", "Token JWT ausente, expirado ou inválido.", False),
        ("Bearer xyz", "/erros/nao-autenticado", "Token JWT ausente, expirado ou inválido.", False),
        ("bearer xyz", "/erros/nao-autenticado", "Token JWT ausente, expirado ou inválido.", False),
    ],
    ids=["sem-token", "esquema-basic", "token-vazio", "token-invalido", "bearer-minusculo"],
)
def test_sem_token_ou_com_token_invalido_segue_401_no_formato_do_projeto(
    client, cabecalho, tipo, detalhe, www_authenticate
):
    headers = {"Authorization": cabecalho} if cabecalho is not None else {}

    resposta = client.get("/api/v1/auth/me", headers=headers)

    assert resposta.status_code == 401  # não 403
    corpo = resposta.json()
    assert (corpo["tipo"], corpo["status"], corpo["detalhe"]) == (tipo, 401, detalhe)
    assert corpo["instancia"] == "/api/v1/auth/me" and corpo["regra"] is None
    assert ("www-authenticate" in resposta.headers) is www_authenticate
    if www_authenticate:
        assert resposta.headers["www-authenticate"] == "Bearer"


def test_o_fluxo_login_copiar_token_e_chamar_rota_protegida(client, token_admin):
    token = client.post(
        "/api/v1/auth/login", json={"login": "admin_teste", "senha": "senha123"}
    ).json()["access_token"]

    resposta = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 200 and resposta.json()["login"] == "admin_teste"
