from sqlalchemy import func, select

from app.models.ativo import Ativo
from app.models.categoria import Categoria
from app.models.fornecedor import Fornecedor


def _payload_valido(categoria, fornecedor, **sobrescritas):
    payload = {
        "nome": "Notebook Dell Latitude 5440",
        "tipo": "HARDWARE",
        "categoria_id": categoria.id,
        "fornecedor_id": fornecedor.id,
        "numero_serie": "BR9K2LM7",
        "data_aquisicao": "2025-03-14",
        "valor_compra": 6000.00,
    }
    payload.update(sobrescritas)
    return payload


def _postar_ativo(client, token, payload):
    return client.post("/api/v1/ativos", headers={"Authorization": f"Bearer {token}"}, json=payload)


def _cabecalho(token):
    return {"Authorization": f"Bearer {token}"}


def _total_ativos(db) -> int:
    return db.scalar(select(func.count()).select_from(Ativo))


def test_criar_ativo_com_categoria_inexistente_retorna_404(client, db, token_admin, fornecedor):
    categoria_fake = type("C", (), {"id": 9999})()
    payload = _payload_valido(categoria_fake, fornecedor, numero_serie="SN-CAT")
    assert _postar_ativo(client, token_admin, payload).status_code == 404
    assert _total_ativos(db) == 0


def test_criar_ativo_com_fornecedor_inexistente_retorna_404(client, db, token_admin, categoria):
    fornecedor_fake = type("F", (), {"id": 9999})()
    payload = _payload_valido(categoria, fornecedor_fake, numero_serie="SN-FORN")
    assert _postar_ativo(client, token_admin, payload).status_code == 404
    assert _total_ativos(db) == 0


def test_obtem_ativo_por_id(client, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-GET")
    ativo_id = _postar_ativo(client, token_admin, payload).json()["id"]

    resposta = client.get(f"/api/v1/ativos/{ativo_id}", headers=_cabecalho(token_admin))
    assert resposta.status_code == 200
    assert resposta.json()["id"] == ativo_id


def test_obtem_ativo_inexistente_retorna_404(client, token_admin):
    resposta = client.get("/api/v1/ativos/9999", headers=_cabecalho(token_admin))
    assert resposta.status_code == 404


def test_atualiza_ativo_existente(client, db, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-PATCH")
    ativo_id = _postar_ativo(client, token_admin, payload).json()["id"]

    resposta = client.patch(
        f"/api/v1/ativos/{ativo_id}",
        headers=_cabecalho(token_admin),
        json={"localizacao": "Sala 10"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["localizacao"] == "Sala 10"
    assert db.get(Ativo, ativo_id).localizacao == "Sala 10"


def test_atualiza_ativo_com_categoria_inexistente_retorna_404(
    client, db, token_admin, categoria, fornecedor
):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-PATCHCAT")
    ativo_id = _postar_ativo(client, token_admin, payload).json()["id"]

    resposta = client.patch(
        f"/api/v1/ativos/{ativo_id}",
        headers=_cabecalho(token_admin),
        json={"categoria_id": 9999},
    )
    assert resposta.status_code == 404
    assert db.get(Ativo, ativo_id).categoria_id == categoria.id


def test_lista_ativos_filtra_por_status_e_tipo(client, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-FILTRO")
    _postar_ativo(client, token_admin, payload)

    params = {"status": "ATIVO", "tipo": "HARDWARE"}
    resposta = client.get("/api/v1/ativos", headers=_cabecalho(token_admin), params=params)
    assert resposta.status_code == 200
    assert resposta.json()["total"] == 1

    resposta_vazia = client.get(
        "/api/v1/ativos", headers=_cabecalho(token_admin), params={"tipo": "SOFTWARE"}
    )
    assert resposta_vazia.json()["total"] == 0


def test_lista_ativos_filtra_por_categoria_e_fornecedor(
    client, db, token_admin, categoria, fornecedor
):
    outra_categoria = Categoria(nome="Servidor", vida_util_meses=60, tipo_aplicavel="HARDWARE")
    outro_fornecedor = Fornecedor(razao_social="Outro Fornecedor LTDA", data_source="sintetico")
    db.add_all([outra_categoria, outro_fornecedor])
    db.commit()
    combinacoes = {
        "SN-CF": (categoria, fornecedor),
        "SN-OF": (categoria, outro_fornecedor),
        "SN-OC": (outra_categoria, fornecedor),
    }
    for serie, (cat, forn) in combinacoes.items():
        payload = _payload_valido(cat, forn, numero_serie=serie)
        assert _postar_ativo(client, token_admin, payload).status_code == 201

    def series(**params):
        corpo = client.get("/api/v1/ativos", headers=_cabecalho(token_admin), params=params).json()
        return sorted(item["numero_serie"] for item in corpo["itens"])

    assert series(categoria_id=categoria.id) == ["SN-CF", "SN-OF"]
    assert series(fornecedor_id=fornecedor.id) == ["SN-CF", "SN-OC"]
    assert series(categoria_id=categoria.id, fornecedor_id=fornecedor.id) == ["SN-CF"]


def test_atualiza_ativo_com_fornecedor_inexistente_retorna_404(
    client, db, token_admin, categoria, fornecedor
):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-PATCHFORN")
    ativo_id = _postar_ativo(client, token_admin, payload).json()["id"]

    resposta = client.patch(
        f"/api/v1/ativos/{ativo_id}", headers=_cabecalho(token_admin), json={"fornecedor_id": 9999}
    )

    assert resposta.status_code == 404
    assert db.get(Ativo, ativo_id).fornecedor_id == fornecedor.id
