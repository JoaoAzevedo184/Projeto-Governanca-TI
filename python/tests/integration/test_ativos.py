from app.models.auditoria import AuditLog


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


def test_ac001_cadastra_ativo_com_status_ativo(client, token_admin, categoria, fornecedor):
    resposta = _postar_ativo(client, token_admin, _payload_valido(categoria, fornecedor))
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "ATIVO"
    assert corpo["id"] is not None


def test_ac002_recusa_numero_serie_duplicado(client, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-DUP")
    assert _postar_ativo(client, token_admin, payload).status_code == 201

    resposta = _postar_ativo(client, token_admin, payload)
    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-001"


def test_ac003_hardware_sem_numero_serie_e_invalido(client, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie=None)
    assert _postar_ativo(client, token_admin, payload).status_code == 422


def test_ac004_software_sem_chave_licenca_e_invalido(client, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, tipo="SOFTWARE", numero_serie=None)
    assert _postar_ativo(client, token_admin, payload).status_code == 422


def test_ac005_recusa_data_aquisicao_futura(client, token_admin, categoria, fornecedor):
    payload = _payload_valido(
        categoria, fornecedor, numero_serie="SN-FUT", data_aquisicao="2099-01-01"
    )
    assert _postar_ativo(client, token_admin, payload).status_code == 422


def test_ac006_recusa_valor_compra_zero(client, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-ZERO", valor_compra=0)
    assert _postar_ativo(client, token_admin, payload).status_code == 422


def test_ac007_herda_vida_util_da_categoria_quando_omitida(
    client, token_admin, categoria, fornecedor
):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-HERDA")
    resposta = _postar_ativo(client, token_admin, payload)
    assert resposta.status_code == 201
    assert resposta.json()["vida_util_meses"] == categoria.vida_util_meses


def test_ac055_auditor_nao_pode_criar_ativo(client, token_auditor, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-AUD")
    assert _postar_ativo(client, token_auditor, payload).status_code == 403


def test_ac056_sem_token_retorna_401(client):
    assert client.get("/api/v1/ativos").status_code == 401


def test_ac057_registra_trilha_de_auditoria(client, db, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-AUDIT")
    assert _postar_ativo(client, token_admin, payload).status_code == 201

    registro = db.query(AuditLog).filter(AuditLog.entidade == "ativo").first()
    assert registro is not None
    assert registro.operacao == "CRIAR"
    assert registro.resultado == "SUCESSO"


def test_lista_ativos_pagina_e_filtra_por_busca(client, token_admin, categoria, fornecedor):
    _postar_ativo(client, token_admin, _payload_valido(categoria, fornecedor, numero_serie="SN-A"))
    _postar_ativo(
        client,
        token_admin,
        _payload_valido(categoria, fornecedor, numero_serie="SN-B", nome="Servidor Dell R440"),
    )

    headers = {"Authorization": f"Bearer {token_admin}"}
    resposta = client.get("/api/v1/ativos", headers=headers, params={"busca": "Servidor"})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["itens"][0]["nome"] == "Servidor Dell R440"
