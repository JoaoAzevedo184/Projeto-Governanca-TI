from prometheus_client import REGISTRY
from sqlalchemy import func, select

from app.models.ativo import Ativo
from app.models.auditoria import AuditLog
from app.models.usuario import Usuario


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


def _total_ativos(db) -> int:
    return db.scalar(select(func.count()).select_from(Ativo))


def test_ac001_cadastra_ativo_com_status_ativo(client, db, token_admin, categoria, fornecedor):
    resposta = _postar_ativo(client, token_admin, _payload_valido(categoria, fornecedor))
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "ATIVO"

    gravado = db.get(Ativo, corpo["id"])
    assert gravado.status == "ATIVO"
    assert gravado.numero_serie == "BR9K2LM7"
    assert gravado.data_source == "manual"  # cadastro direto pela API, não planilha


def test_ac002_recusa_numero_serie_duplicado(client, db, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-DUP")
    assert _postar_ativo(client, token_admin, payload).status_code == 201

    resposta = _postar_ativo(client, token_admin, payload)
    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-001"
    assert _total_ativos(db) == 1


def test_ac003_hardware_sem_numero_serie_e_invalido(client, db, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie=None)
    assert _postar_ativo(client, token_admin, payload).status_code == 422
    assert _total_ativos(db) == 0


def test_ac004_software_sem_chave_licenca_e_invalido(
    client, db, token_admin, categoria, fornecedor
):
    payload = _payload_valido(categoria, fornecedor, tipo="SOFTWARE", numero_serie=None)
    assert _postar_ativo(client, token_admin, payload).status_code == 422
    assert _total_ativos(db) == 0


def test_ac005_recusa_data_aquisicao_futura(client, db, token_admin, categoria, fornecedor):
    payload = _payload_valido(
        categoria, fornecedor, numero_serie="SN-FUT", data_aquisicao="2099-01-01"
    )
    assert _postar_ativo(client, token_admin, payload).status_code == 422
    assert _total_ativos(db) == 0


def test_ac006_recusa_valor_compra_zero(client, db, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-ZERO", valor_compra=0)
    assert _postar_ativo(client, token_admin, payload).status_code == 422
    assert _total_ativos(db) == 0


def test_ac007_herda_vida_util_da_categoria_quando_omitida(
    client, db, token_admin, categoria, fornecedor
):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-HERDA")
    resposta = _postar_ativo(client, token_admin, payload)
    assert resposta.status_code == 201
    assert resposta.json()["vida_util_meses"] == 60  # categoria "Notebook" do conftest
    assert db.get(Ativo, resposta.json()["id"]).vida_util_meses == 60


def test_ac055_auditor_nao_pode_criar_ativo(client, db, token_auditor, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-AUD")
    assert _postar_ativo(client, token_auditor, payload).status_code == 403
    assert _total_ativos(db) == 0


def test_ac056_sem_token_retorna_401(client):
    assert client.get("/api/v1/ativos").status_code == 401


def test_ac057_registra_trilha_de_auditoria(client, db, token_admin, categoria, fornecedor):
    payload = _payload_valido(categoria, fornecedor, numero_serie="SN-AUDIT")
    resposta = _postar_ativo(client, token_admin, payload)
    assert resposta.status_code == 201

    registro = db.query(AuditLog).filter(AuditLog.entidade == "ativo").one()
    assert registro.entidade_id == resposta.json()["id"]
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


CHAVE = "ABCD-1234-EFGH-WXYZ"


def _violadas(regra: str) -> float:
    return REGISTRY.get_sample_value("itam_regras_violadas_total", {"regra": regra}) or 0.0


def _software(categoria, fornecedor, chave=CHAVE, **sobrescritas):
    campos = {"nome": "Suite Escritorio", "tipo": "SOFTWARE", "numero_serie": None}
    return _payload_valido(
        categoria, fornecedor, **{**campos, "chave_licenca": chave, **sobrescritas}
    )


def test_ac067_recusa_chave_licenca_duplicada_na_auditoria_e_na_metrica(
    client, db, token_admin, categoria, fornecedor
):
    primeiro = _postar_ativo(client, token_admin, _software(categoria, fornecedor))
    assert primeiro.status_code == 201
    antes = _violadas("BR-039")

    resposta = _postar_ativo(client, token_admin, _software(categoria, fornecedor, nome="Outro"))

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-039"
    assert _total_ativos(db) == 1
    recusas = db.scalars(select(AuditLog).where(AuditLog.resultado == "RECUSADO")).all()
    assert len(recusas) == 1
    recusa = recusas[0]
    assert (recusa.operacao, recusa.entidade, recusa.regra_violada) == ("CRIAR", "ativo", "BR-039")
    assert recusa.usuario_id == db.scalar(select(Usuario.id).where(Usuario.login == "admin_teste"))
    assert recusa.detalhe == {"ativo_conflitante_id": primeiro.json()["id"]}
    assert _violadas("BR-039") == antes + 1
    # RI-08: a chave completa não sai na resposta nem na trilha.
    assert CHAVE not in resposta.text
    assert CHAVE not in str(recusa.detalhe)


def test_ac067_a_chave_vale_para_qualquer_ativo_e_tambem_entre_tipos(
    client, db, token_admin, categoria, fornecedor
):
    assert _postar_ativo(client, token_admin, _software(categoria, fornecedor)).status_code == 201

    hardware_com_a_mesma_chave = _payload_valido(
        categoria, fornecedor, numero_serie="SN-HW-1", chave_licenca=CHAVE
    )
    resposta = _postar_ativo(client, token_admin, hardware_com_a_mesma_chave)

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-039"
    assert _total_ativos(db) == 1


def test_ac067_ativos_sem_chave_continuam_aceitos(client, db, token_admin, categoria, fornecedor):
    for serie in ("SN-A", "SN-B"):
        payload = _payload_valido(categoria, fornecedor, numero_serie=serie)
        assert _postar_ativo(client, token_admin, payload).status_code == 201

    assert db.scalar(select(func.count()).where(Ativo.chave_licenca.is_(None))) == 2


def test_ac067_chave_diferente_so_no_caso_das_letras_e_aceita(
    client, db, token_admin, categoria, fornecedor
):
    """A comparação é exata: o banco não normaliza caixa, e o teste fixa esse comportamento."""
    assert _postar_ativo(client, token_admin, _software(categoria, fornecedor)).status_code == 201

    outra = _software(categoria, fornecedor, chave=CHAVE.lower(), nome="Outro")

    assert _postar_ativo(client, token_admin, outra).status_code == 201
    assert _total_ativos(db) == 2


def test_ac067_recusa_na_checagem_previa_nao_consome_id(
    client, db, token_admin, categoria, fornecedor
):
    primeiro = _postar_ativo(client, token_admin, _software(categoria, fornecedor)).json()["id"]
    assert (
        _postar_ativo(client, token_admin, _software(categoria, fornecedor, nome="Dup")).status_code
        == 409
    )

    seguinte = _postar_ativo(client, token_admin, _software(categoria, fornecedor, chave="OUTRA-1"))

    assert seguinte.json()["id"] == primeiro + 1  # a recusa não chegou a inserir (sem buraco)
