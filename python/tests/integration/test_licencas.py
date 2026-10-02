"""Controle de licenças (FR-004): AC-021, AC-024, AC-025, AC-026, BR-018 a BR-021, RI-08."""

from datetime import date, timedelta

import pytest
from sqlalchemy import func, select

from app.models.auditoria import AuditLog
from app.models.licenca import Licenca, LicencaVinculo

VALIDA = "2099-12-31"
INICIO = "2025-01-01"


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _ativo(client, token, categoria, fornecedor, tipo, nome, **extra):
    identificador = (
        {"numero_serie": f"SN-{nome}"} if tipo == "HARDWARE" else {"chave_licenca": f"K-{nome}"}
    )
    resposta = client.post(
        "/api/v1/ativos",
        headers=_headers(token),
        json={
            "nome": f"Ativo {nome}",
            "tipo": tipo,
            "categoria_id": categoria.id,
            "fornecedor_id": fornecedor.id,
            "data_aquisicao": "2025-01-10",
            "valor_compra": "1000.00",
            **identificador,
            **extra,
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


@pytest.fixture
def maquinas(client, token_admin, categoria, fornecedor):
    return [
        _ativo(client, token_admin, categoria, fornecedor, "HARDWARE", f"HW{n}") for n in range(4)
    ]


@pytest.fixture
def software_id(client, token_admin, categoria, fornecedor):
    return _ativo(client, token_admin, categoria, fornecedor, "SOFTWARE", "SW1")


def _corpo(fornecedor, **sobrescritas):
    corpo = {
        "tipo_licenciamento": "SUBSCRICAO",
        "software": "Suite Escritorio",
        "fornecedor_id": fornecedor.id,
        "chave_licenca": "ABCD-1234-EFGH-A3F9",
        "quantidade_contratada": 2,
        "data_inicio_vigencia": INICIO,
        "data_expiracao": VALIDA,
        "valor_total": "1200.00",
        **sobrescritas,
    }
    return {chave: valor for chave, valor in corpo.items() if valor is not ...}


def _criar(client, token, fornecedor, **sobrescritas):
    return client.post(
        "/api/v1/licencas", headers=_headers(token), json=_corpo(fornecedor, **sobrescritas)
    )


@pytest.fixture
def licenca_id(client, token_admin, fornecedor):
    resposta = _criar(client, token_admin, fornecedor)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


def _vincular(client, token, licenca_id, ativo_id, **extra):
    return client.post(
        f"/api/v1/licencas/{licenca_id}/vinculos",
        headers=_headers(token),
        json={"ativo_id": ativo_id, **extra},
    )


def _obter(client, token, licenca_id):
    return client.get(f"/api/v1/licencas/{licenca_id}", headers=_headers(token)).json()


def _total(db, modelo) -> int:
    return db.scalar(select(func.count()).select_from(modelo))


def _recusas(db):
    return [
        (a.entidade, a.operacao, a.regra_violada)
        for a in db.scalars(select(AuditLog).where(AuditLog.resultado == "RECUSADO"))
    ]


# --- criação (FR-004) ---


def test_cria_licenca_subscricao_com_bloco_derivado(client, token_admin, fornecedor):
    resposta = _criar(client, token_admin, fornecedor)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["tipo_licenciamento"] == "SUBSCRICAO"
    assert corpo["software"] == "Suite Escritorio"
    assert corpo["ativo_id"] is None
    assert corpo["valor_total"] == "1200.00"  # dinheiro como string (item 9 da resolução)
    assert corpo["quantidade_contratada"] == 2
    assert corpo["quantidade_em_uso"] == 0
    assert corpo["saldo"] == 2
    assert corpo["dias_para_expiracao"] == (date(2099, 12, 31) - date.today()).days
    assert corpo["data_source"] == "manual"
    assert "status_conformidade" not in corpo and "alertas" not in corpo  # FR-007, Sprint 4


def test_cria_licenca_perpetua_apontando_para_ativo_software(
    client, token_admin, fornecedor, software_id
):
    resposta = _criar(
        client,
        token_admin,
        fornecedor,
        tipo_licenciamento="PERPETUA",
        ativo_id=software_id,
        software=...,
        valor_total=...,
    )

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["ativo_id"] == software_id
    assert resposta.json()["software"] is None
    assert resposta.json()["valor_total"] is None  # o valor patrimonial fica no ativo (ADR-012)


def test_cria_licenca_oem_sem_valor(client, token_admin, fornecedor):
    resposta = _criar(client, token_admin, fornecedor, tipo_licenciamento="OEM", valor_total=...)

    assert resposta.status_code == 201
    assert resposta.json()["valor_total"] is None


def test_perpetua_apontando_para_hardware_e_recusada(client, db, token_admin, fornecedor, maquinas):
    resposta = _criar(
        client,
        token_admin,
        fornecedor,
        tipo_licenciamento="PERPETUA",
        ativo_id=maquinas[0],
        software=...,
        valor_total=...,
    )

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "FR-004"
    assert _total(db, Licenca) == 0
    assert _recusas(db) == [("licenca", "CRIAR", "FR-004")]


@pytest.mark.parametrize(
    "sobrescritas",
    [
        {"tipo_licenciamento": "PERPETUA", "software": ..., "valor_total": ...},  # sem ativo_id
        {"tipo_licenciamento": "PERPETUA", "ativo_id": 1},  # com software e valor
        {"tipo_licenciamento": "SUBSCRICAO", "ativo_id": 1},  # subscrição não é ativo
        {"tipo_licenciamento": "SUBSCRICAO", "software": ...},  # sem nome
        {"tipo_licenciamento": "SUBSCRICAO", "valor_total": ...},  # sem valor
        {"tipo_licenciamento": "OEM"},  # OEM não tem valor
        {"tipo_licenciamento": "OEM", "software": ..., "valor_total": ...},  # sem nome
        {"tipo_licenciamento": "OEM", "ativo_id": 1, "valor_total": ...},
        {"tipo_licenciamento": "DE_GRACA"},
        {"quantidade_contratada": 0},
        {"valor_total": "0"},
        {"chave_licenca": ""},
        {"data_inicio_vigencia": (date.today() + timedelta(days=1)).isoformat()},
        {"data_expiracao": "ontem"},
    ],
)
def test_forma_invalida_da_licenca_retorna_422(client, db, token_admin, fornecedor, sobrescritas):
    resposta = _criar(client, token_admin, fornecedor, **sobrescritas)

    assert resposta.status_code == 422, resposta.text
    assert _total(db, Licenca) == 0


def test_ac024_expiracao_nao_posterior_ao_inicio_e_recusada(client, db, token_admin, fornecedor):
    for expiracao in (INICIO, "2024-12-31"):
        resposta = _criar(client, token_admin, fornecedor, data_expiracao=expiracao)

        assert resposta.status_code == 409
        assert resposta.json()["regra"] == "BR-019"
    assert _total(db, Licenca) == 0
    assert _recusas(db) == [("licenca", "CRIAR", "BR-019")] * 2


def test_referencias_inexistentes_na_criacao_retornam_404(client, token_admin, fornecedor):
    assert _criar(client, token_admin, fornecedor, fornecedor_id=999).status_code == 404
    perpetua = _criar(
        client,
        token_admin,
        fornecedor,
        tipo_licenciamento="PERPETUA",
        ativo_id=999,
        software=...,
        valor_total=...,
    )
    assert perpetua.status_code == 404


# --- vínculos: BR-018, BR-020, BR-021, AC-026 ---


def test_vincula_licenca_a_maquina_e_deriva_quantidade_em_uso(
    client, db, token_admin, licenca_id, maquinas
):
    primeira = _vincular(client, token_admin, licenca_id, maquinas[0])

    assert primeira.status_code == 201, primeira.text
    assert primeira.json()["ativo_id"] == maquinas[0]
    assert primeira.json()["ativo_vinculo"] is True
    assert primeira.json()["data_vinculo"] == date.today().isoformat()
    assert primeira.json()["data_source"] == "manual"
    licenca = _obter(client, token_admin, licenca_id)
    assert (licenca["quantidade_em_uso"], licenca["saldo"]) == (1, 1)
    assert not hasattr(Licenca, "quantidade_em_uso")  # BR-021: derivada, nunca coluna


def test_vinculo_aceita_data_de_vinculo_informada(client, token_admin, licenca_id, maquinas):
    resposta = _vincular(client, token_admin, licenca_id, maquinas[0], data_vinculo="2025-03-01")

    assert resposta.json()["data_vinculo"] == "2025-03-01"


def test_ac021_vinculo_acima_do_contratado_e_bloqueado_e_auditado(
    client, db, token_admin, licenca_id, maquinas
):
    assert _vincular(client, token_admin, licenca_id, maquinas[0]).status_code == 201
    assert _vincular(client, token_admin, licenca_id, maquinas[1]).status_code == 201  # lotada

    excedente = _vincular(client, token_admin, licenca_id, maquinas[2])

    assert excedente.status_code == 409
    assert excedente.json()["regra"] == "BR-018"
    assert _total(db, LicencaVinculo) == 2
    assert _obter(client, token_admin, licenca_id)["quantidade_em_uso"] == 2
    recusa = db.scalars(select(AuditLog).where(AuditLog.resultado == "RECUSADO")).one()
    assert (recusa.entidade, recusa.operacao, recusa.regra_violada) == (
        "licenca_vinculo",
        "CRIAR",
        "BR-018",
    )
    assert recusa.detalhe == {"licenca_id": licenca_id, "ativo_id": maquinas[2]}


def test_ac025_licenca_vencida_nao_recebe_vinculo(client, db, token_admin, fornecedor, maquinas):
    vencida = _criar(
        client,
        token_admin,
        fornecedor,
        data_inicio_vigencia="2020-01-01",
        data_expiracao="2020-12-31",
    ).json()
    assert vencida["dias_para_expiracao"] < 0

    resposta = _vincular(client, token_admin, vencida["id"], maquinas[0])

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-020"
    assert _total(db, LicencaVinculo) == 0
    assert _recusas(db) == [("licenca_vinculo", "CRIAR", "BR-020")]


def test_br020_licenca_que_vence_hoje_ainda_recebe_vinculo(
    client, token_admin, fornecedor, maquinas
):
    licenca = _criar(
        client, token_admin, fornecedor, data_expiracao=date.today().isoformat()
    ).json()

    assert licenca["dias_para_expiracao"] == 0
    assert _vincular(client, token_admin, licenca["id"], maquinas[0]).status_code == 201


def test_ac026_desvinculo_decrementa_a_quantidade_em_uso_e_libera_o_assento(
    client, db, token_admin, licenca_id, maquinas
):
    _vincular(client, token_admin, licenca_id, maquinas[0])
    _vincular(client, token_admin, licenca_id, maquinas[1])
    assert _obter(client, token_admin, licenca_id)["quantidade_em_uso"] == 2

    resposta = client.delete(
        f"/api/v1/licencas/{licenca_id}/vinculos/{maquinas[0]}", headers=_headers(token_admin)
    )

    assert resposta.status_code == 204
    licenca = _obter(client, token_admin, licenca_id)
    assert (licenca["quantidade_em_uso"], licenca["saldo"]) == (1, 1)
    assert _total(db, LicencaVinculo) == 2  # desvínculo lógico: nada é apagado (RI-06)
    assert _vincular(client, token_admin, licenca_id, maquinas[2]).status_code == 201
    # a mesma máquina volta a poder receber a licença depois do desvínculo
    client.delete(
        f"/api/v1/licencas/{licenca_id}/vinculos/{maquinas[1]}", headers=_headers(token_admin)
    )
    assert _vincular(client, token_admin, licenca_id, maquinas[1]).status_code == 201


def test_listagem_de_vinculos_traz_ativos_e_desvinculados(
    client, token_admin, licenca_id, maquinas
):
    _vincular(client, token_admin, licenca_id, maquinas[0])
    _vincular(client, token_admin, licenca_id, maquinas[1])
    client.delete(
        f"/api/v1/licencas/{licenca_id}/vinculos/{maquinas[0]}", headers=_headers(token_admin)
    )

    resposta = client.get(f"/api/v1/licencas/{licenca_id}/vinculos", headers=_headers(token_admin))

    vinculos = resposta.json()
    assert [(v["ativo_id"], v["ativo_vinculo"]) for v in vinculos] == [
        (maquinas[1], True),
        (maquinas[0], False),
    ]


def test_vinculo_duplicado_na_mesma_maquina_e_recusado(
    client, db, token_admin, licenca_id, maquinas
):
    _vincular(client, token_admin, licenca_id, maquinas[0])

    repetido = _vincular(client, token_admin, licenca_id, maquinas[0])

    assert repetido.status_code == 409
    assert repetido.json()["regra"] == "FR-004"
    assert _obter(client, token_admin, licenca_id)["quantidade_em_uso"] == 1


def test_vinculo_so_aceita_maquina_hardware(client, db, token_admin, licenca_id, software_id):
    resposta = _vincular(client, token_admin, licenca_id, software_id)

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "FR-004"
    assert _total(db, LicencaVinculo) == 0


def test_referencias_inexistentes_nos_vinculos_retornam_404(
    client, token_admin, licenca_id, maquinas
):
    assert _vincular(client, token_admin, 999, maquinas[0]).status_code == 404
    assert _vincular(client, token_admin, licenca_id, 999).status_code == 404
    assert (
        client.get("/api/v1/licencas/999/vinculos", headers=_headers(token_admin)).status_code
        == 404
    )
    sem_vinculo = client.delete(
        f"/api/v1/licencas/{licenca_id}/vinculos/{maquinas[0]}", headers=_headers(token_admin)
    )
    assert sem_vinculo.status_code == 404
    assert (
        client.delete("/api/v1/licencas/999/vinculos/1", headers=_headers(token_admin)).status_code
        == 404
    )


def test_data_de_vinculo_futura_retorna_422(client, token_admin, licenca_id, maquinas):
    amanha = (date.today() + timedelta(days=1)).isoformat()

    resposta = _vincular(client, token_admin, licenca_id, maquinas[0], data_vinculo=amanha)

    assert resposta.status_code == 422


# --- consulta, edição ---


def test_lista_licencas_com_envelope_filtros_e_chave_mascarada(
    client, token_admin, fornecedor, licenca_id
):
    _criar(
        client,
        token_admin,
        fornecedor,
        tipo_licenciamento="OEM",
        valor_total=...,
        chave_licenca="OEM-0000-ZZZZ",
    )

    todas = client.get("/api/v1/licencas", headers=_headers(token_admin)).json()
    oem = client.get(
        "/api/v1/licencas?tipo_licenciamento=OEM&tamanho=1", headers=_headers(token_admin)
    ).json()
    outro = client.get("/api/v1/licencas?fornecedor_id=999", headers=_headers(token_admin)).json()

    assert (todas["pagina"], todas["tamanho"], todas["total"], todas["total_paginas"]) == (
        1,
        20,
        2,
        1,
    )
    assert [i["chave_licenca"] for i in todas["itens"]] == ["****-****-A3F9", "****-****-ZZZZ"]
    assert oem["total"] == 1 and oem["itens"][0]["tipo_licenciamento"] == "OEM"
    assert outro == {"itens": [], "pagina": 1, "tamanho": 20, "total": 0, "total_paginas": 0}


def test_listagem_traz_a_quantidade_em_uso_de_cada_licenca(
    client, token_admin, fornecedor, licenca_id, maquinas
):
    segunda = _criar(client, token_admin, fornecedor, quantidade_contratada=5).json()["id"]
    _vincular(client, token_admin, licenca_id, maquinas[0])
    _vincular(client, token_admin, segunda, maquinas[0])
    _vincular(client, token_admin, segunda, maquinas[1])

    itens = client.get("/api/v1/licencas", headers=_headers(token_admin)).json()["itens"]

    assert [(i["id"], i["quantidade_em_uso"], i["saldo"]) for i in itens] == [
        (licenca_id, 1, 1),
        (segunda, 2, 3),
    ]


def test_ri08_chave_completa_so_no_detalhe_e_so_para_admin(
    request, client, licenca_id, token_admin, token_operador, token_gestor, token_auditor
):
    completa = "ABCD-1234-EFGH-A3F9"

    admin = _obter(client, token_admin, licenca_id)
    assert admin["chave_licenca"] == completa
    for token in (token_operador, token_gestor, token_auditor):
        assert _obter(client, token, licenca_id)["chave_licenca"] == "****-****-A3F9"

    listagem = client.get("/api/v1/licencas", headers=_headers(token_admin)).json()["itens"]
    assert listagem[0]["chave_licenca"] == "****-****-A3F9"  # listagem: mascarada até para ADMIN


def test_ri08_chave_do_ativo_software_segue_a_mesma_regra(
    client, token_admin, token_operador, software_id
):
    detalhe_admin = client.get(f"/api/v1/ativos/{software_id}", headers=_headers(token_admin))
    detalhe_operador = client.get(f"/api/v1/ativos/{software_id}", headers=_headers(token_operador))
    listagem = client.get("/api/v1/ativos?tipo=SOFTWARE", headers=_headers(token_admin)).json()

    assert detalhe_admin.json()["chave_licenca"] == "K-SW1"  # curta demais: sempre mascarada
    assert detalhe_operador.json()["chave_licenca"] == "****-****-****"
    assert listagem["itens"][0]["chave_licenca"] == "****-****-****"


def test_ri08_chave_longa_do_ativo_aparece_completa_so_para_admin_no_detalhe(
    client, token_admin, token_operador, categoria, fornecedor
):
    ativo = _ativo(
        client,
        token_admin,
        categoria,
        fornecedor,
        "SOFTWARE",
        "LONGO",
        chave_licenca="WXYZ-9876-QRST",
    )

    assert (
        client.get(f"/api/v1/ativos/{ativo}", headers=_headers(token_admin)).json()["chave_licenca"]
        == "WXYZ-9876-QRST"
    )
    mascarada = client.get(f"/api/v1/ativos/{ativo}", headers=_headers(token_operador)).json()
    assert mascarada["chave_licenca"] == "****-****-QRST"
    assert client.get("/api/v1/ativos", headers=_headers(token_admin)).json()["itens"][0][
        "chave_licenca"
    ] in (None, "****-****-QRST")


def test_licenca_inexistente_retorna_404(client, token_admin):
    assert client.get("/api/v1/licencas/999", headers=_headers(token_admin)).status_code == 404
    atualizacao = client.patch(
        "/api/v1/licencas/999", headers=_headers(token_admin), json={"quantidade_contratada": 3}
    )
    assert atualizacao.status_code == 404


def test_operador_edita_licenca_e_admin_nao_precisa_repetir_campos(
    client, db, token_operador, licenca_id, fornecedor
):
    resposta = client.patch(
        f"/api/v1/licencas/{licenca_id}",
        headers=_headers(token_operador),
        json={"quantidade_contratada": 10, "data_expiracao": "2100-06-30"},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert (corpo["quantidade_contratada"], corpo["saldo"], corpo["data_expiracao"]) == (
        10,
        10,
        "2100-06-30",
    )
    assert corpo["chave_licenca"] == "****-****-A3F9"  # OPERADOR não vê a chave completa


def test_edicao_atualiza_fornecedor_e_chave(client, token_admin, licenca_id, db):
    from app.models.fornecedor import Fornecedor

    outro = Fornecedor(razao_social="Outro Fornecedor", data_source="manual")
    db.add(outro)
    db.commit()

    resposta = client.patch(
        f"/api/v1/licencas/{licenca_id}",
        headers=_headers(token_admin),
        json={"fornecedor_id": outro.id, "chave_licenca": "NOVA-CHAVE-0001"},
    )

    assert resposta.json()["fornecedor_id"] == outro.id
    assert resposta.json()["chave_licenca"] == "NOVA-CHAVE-0001"
    assert (
        client.patch(
            f"/api/v1/licencas/{licenca_id}",
            headers=_headers(token_admin),
            json={"fornecedor_id": 999},
        ).status_code
        == 404
    )


def test_br019_edicao_que_inverte_as_datas_e_recusada(client, db, token_admin, licenca_id):
    resposta = client.patch(
        f"/api/v1/licencas/{licenca_id}",
        headers=_headers(token_admin),
        json={"data_inicio_vigencia": "2100-01-01"},
    )

    assert resposta.status_code == 422  # início futuro: validação de schema
    resposta = client.patch(
        f"/api/v1/licencas/{licenca_id}",
        headers=_headers(token_admin),
        json={"data_expiracao": INICIO},
    )
    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-019"
    assert _recusas(db) == [("licenca", "ATUALIZAR", "BR-019")]


def test_br018_reduzir_o_contratado_abaixo_do_uso_e_recusado(
    client, db, token_admin, licenca_id, maquinas
):
    _vincular(client, token_admin, licenca_id, maquinas[0])
    _vincular(client, token_admin, licenca_id, maquinas[1])

    resposta = client.patch(
        f"/api/v1/licencas/{licenca_id}",
        headers=_headers(token_admin),
        json={"quantidade_contratada": 1},
    )

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-018"
    assert _obter(client, token_admin, licenca_id)["quantidade_contratada"] == 2
    assert _recusas(db) == [("licenca", "ATUALIZAR", "BR-018")]


def test_ac057_escritas_de_licenca_registram_auditoria(
    client, db, token_admin, fornecedor, maquinas
):
    licenca = _criar(client, token_admin, fornecedor).json()["id"]
    vinculo = _vincular(client, token_admin, licenca, maquinas[0]).json()["id"]
    client.patch(
        f"/api/v1/licencas/{licenca}",
        headers=_headers(token_admin),
        json={"quantidade_contratada": 3},
    )
    client.delete(
        f"/api/v1/licencas/{licenca}/vinculos/{maquinas[0]}", headers=_headers(token_admin)
    )

    registros = {
        (a.operacao, a.entidade, a.entidade_id)
        for a in db.scalars(select(AuditLog).where(AuditLog.entidade.like("licenca%")))
    }
    assert registros == {
        ("CRIAR", "licenca", licenca),
        ("CRIAR", "licenca_vinculo", vinculo),
        ("ATUALIZAR", "licenca", licenca),
        ("EXCLUIR", "licenca_vinculo", vinculo),
    }
