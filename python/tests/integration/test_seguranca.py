"""Matriz RBAC do FR-015, restrita às rotas que existem hoje (docs/spec/contrato-api.md §6).

Permitido = resposta não é 401 nem 403 (o corpo pode falhar por outro motivo,
mas a autorização não pode ser o que barra). Negado = 403. Sem token = 401
em qualquer rota, inclusive as de leitura.
"""

import io

import pytest

PERFIS = ["admin", "operador", "gestor", "auditor"]


def _csv_valido(categoria_nome: str, fornecedor_nome: str, sufixo: str) -> bytes:
    linhas = [
        "nome,tipo,categoria,fornecedor,numero_serie,data_aquisicao,valor_compra",
        f"Notebook RBAC {sufixo},HARDWARE,{categoria_nome},{fornecedor_nome},"
        f"SN-RBAC-IMPORT-{sufixo},2025-01-10,1000.00",
    ]
    return ("\n".join(linhas) + "\n").encode("utf-8")


@pytest.fixture
def ativo_existente(client, token_admin, categoria, fornecedor):
    payload = {
        "nome": "Notebook RBAC Base",
        "tipo": "HARDWARE",
        "categoria_id": categoria.id,
        "fornecedor_id": fornecedor.id,
        "numero_serie": "SN-RBAC-BASE",
        "data_aquisicao": "2025-01-10",
        "valor_compra": 1000.00,
    }
    resposta = client.post(
        "/api/v1/ativos", headers={"Authorization": f"Bearer {token_admin}"}, json=payload
    )
    return resposta.json()["id"]


def _rotas(cat_id: int, forn_id: int, ativo_id: int, cat_nome: str, forn_nome: str):
    """(método, path, payload_por_perfil, kind, perfis_permitidos)."""
    todos = set(PERFIS)
    return [
        ("GET", "/api/v1/categorias", None, "json", todos),
        (
            "POST",
            "/api/v1/categorias",
            lambda p: {
                "nome": f"Categoria RBAC {p}",
                "vida_util_meses": 36,
                "tipo_aplicavel": "HARDWARE",
            },
            "json",
            {"admin"},
        ),
        ("GET", f"/api/v1/categorias/{cat_id}", None, "json", todos),
        (
            "PATCH",
            f"/api/v1/categorias/{cat_id}",
            lambda p: {"descricao": f"RBAC {p}"},
            "json",
            {"admin"},
        ),
        ("GET", "/api/v1/fornecedores", None, "json", todos),
        (
            "POST",
            "/api/v1/fornecedores",
            lambda p: {"razao_social": f"Fornecedor RBAC {p}"},
            "json",
            {"admin"},
        ),
        ("GET", "/api/v1/setores", None, "json", todos),
        ("POST", "/api/v1/setores", lambda p: {"nome": f"Setor RBAC {p}"}, "json", {"admin"}),
        ("GET", "/api/v1/responsaveis", None, "json", todos),
        (
            "POST",
            "/api/v1/responsaveis",
            lambda p: {"nome": f"Responsavel RBAC {p}"},
            "json",
            {"admin", "operador"},
        ),
        ("GET", "/api/v1/ativos", None, "json", todos),
        ("GET", f"/api/v1/ativos/{ativo_id}", None, "json", todos),
        (
            "POST",
            "/api/v1/ativos",
            lambda p: {
                "nome": f"Notebook RBAC {p}",
                "tipo": "HARDWARE",
                "categoria_id": cat_id,
                "fornecedor_id": forn_id,
                "numero_serie": f"SN-RBAC-{p}",
                "data_aquisicao": "2025-01-10",
                "valor_compra": 1000.00,
            },
            "json",
            {"admin", "operador"},
        ),
        (
            "PATCH",
            f"/api/v1/ativos/{ativo_id}",
            lambda p: {"localizacao": f"Sala {p}"},
            "json",
            {"admin", "operador"},
        ),
        (
            "POST",
            "/api/v1/importacoes",
            lambda p: _csv_valido(cat_nome, forn_nome, p),
            "arquivo",
            {"admin"},
        ),
        ("GET", "/api/v1/importacoes", None, "json", todos),
        ("GET", "/api/v1/auth/me", None, "json", todos),
    ]


def _tokens(request):
    return {
        "admin": request.getfixturevalue("token_admin"),
        "operador": request.getfixturevalue("token_operador"),
        "gestor": request.getfixturevalue("token_gestor"),
        "auditor": request.getfixturevalue("token_auditor"),
    }


def _requisitar(client, metodo, path, token, payload, kind, perfil):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if kind == "arquivo":
        conteudo = payload(perfil) if callable(payload) else None
        arquivos = {"arquivo": ("inventario.csv", io.BytesIO(conteudo), "text/csv")}
        return client.request(metodo, path, headers=headers, files=arquivos)
    corpo = payload(perfil) if callable(payload) else payload
    return client.request(metodo, path, headers=headers, json=corpo)


@pytest.mark.parametrize("perfil", PERFIS)
def test_matriz_rbac_por_perfil(request, client, categoria, fornecedor, ativo_existente, perfil):
    tokens = _tokens(request)
    rotas = _rotas(
        categoria.id, fornecedor.id, ativo_existente, categoria.nome, fornecedor.razao_social
    )

    for metodo, path, payload, kind, permitidos in rotas:
        resposta = _requisitar(client, metodo, path, tokens[perfil], payload, kind, perfil)
        contexto = f"{perfil} {metodo} {path} -> {resposta.status_code}: {resposta.text}"
        if perfil in permitidos:
            assert resposta.status_code not in (401, 403), contexto
        else:
            assert resposta.status_code == 403, contexto


def test_matriz_rbac_sem_token_retorna_401(client, categoria, fornecedor, ativo_existente):
    rotas = _rotas(
        categoria.id, fornecedor.id, ativo_existente, categoria.nome, fornecedor.razao_social
    )
    for metodo, path, payload, kind, _permitidos in rotas:
        resposta = _requisitar(client, metodo, path, None, payload, kind, "sem_token")
        assert resposta.status_code == 401, f"{metodo} {path} sem token -> {resposta.status_code}"
