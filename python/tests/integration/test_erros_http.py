"""Erros fora das regras de negócio no formato único da API (docs/spec/padrao-de-erros.md).

Achados dos testes de contrato (Sprint 5): inteiro além de 32 bits num id virava 500 (erro do
driver), e os erros do próprio framework (rota inexistente, token ausente, corpo ilegível) saíam
como `{"detail": ...}`, fora do formato e do contrato.
"""

import pytest

CHAVES = {"tipo", "titulo", "status", "detalhe", "instancia", "regra", "erros"}


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "rota",
    [
        "/api/v1/ativos/99999999999",
        "/api/v1/categorias/99999999999",
        "/api/v1/licencas/99999999999",
        "/api/v1/licencas/99999999999/vinculos",
        "/api/v1/riscos/99999999999",
        "/api/v1/recomendacoes/99999999999",
        "/api/v1/importacoes/99999999999",
    ],
)
def test_id_alem_de_32_bits_na_rota_e_422_e_nao_500(client, token_admin, rota):
    resposta = client.get(rota, headers=_headers(token_admin))

    assert resposta.status_code == 422
    corpo = resposta.json()
    assert set(corpo) == CHAVES and corpo["regra"] is None
    assert "intervalo" in corpo["detalhe"]
    assert "integer" not in resposta.text.lower() and "psycopg" not in resposta.text.lower()


def test_id_alem_de_32_bits_no_corpo_e_422_e_nada_e_gravado(
    client, db, token_admin, categoria, fornecedor
):
    resposta = client.post(
        "/api/v1/ativos",
        headers=_headers(token_admin),
        json={
            "nome": "Notebook",
            "tipo": "HARDWARE",
            "categoria_id": 99999999999,
            "fornecedor_id": fornecedor.id,
            "numero_serie": "SN-GRANDE",
            "data_aquisicao": "2025-01-10",
            "valor_compra": "10.00",
        },
    )

    assert resposta.status_code == 422
    db.rollback()  # o teste compartilha a sessão; em produção cada requisição tem a sua
    assert client.get("/api/v1/ativos", headers=_headers(token_admin)).json()["total"] == 0


def test_rota_inexistente_e_404_no_formato_da_api(client):
    resposta = client.get("/api/v1/nao-existe")

    assert resposta.status_code == 404
    corpo = resposta.json()
    assert set(corpo) == CHAVES
    assert (corpo["tipo"], corpo["titulo"], corpo["instancia"]) == (
        "/erros/http-404",
        "Recurso não encontrado",
        "/api/v1/nao-existe",
    )


def test_metodo_nao_permitido_e_405_no_formato_da_api(client, token_admin):
    resposta = client.delete("/api/v1/ativos/1", headers=_headers(token_admin))

    assert resposta.status_code == 405
    assert set(resposta.json()) == CHAVES and resposta.json()["titulo"] == "Método não permitido"


def test_token_ausente_e_401_no_formato_da_api_e_mantem_o_cabecalho_www_authenticate(client):
    resposta = client.get("/api/v1/ativos")

    assert resposta.status_code == 401
    assert set(resposta.json()) == CHAVES and resposta.json()["titulo"] == "Não autenticado"
    assert resposta.headers["www-authenticate"] == "Bearer"


def test_corpo_multipart_ilegivel_e_400_no_formato_da_api(client, token_admin):
    resposta = client.post(
        "/api/v1/importacoes",
        headers={**_headers(token_admin), "Content-Type": "multipart/form-data; boundary=xyz"},
        content=b"isto nao e multipart",
    )

    assert resposta.status_code in (400, 422)
    assert set(resposta.json()) == CHAVES
