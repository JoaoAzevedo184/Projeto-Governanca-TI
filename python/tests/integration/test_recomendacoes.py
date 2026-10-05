"""Recomendação rastreável (FR-013): AC-051 e BR-027.

BR-027 é do serviço (invariantes.md): recomendação e evidências nascem na mesma transação."""

from datetime import date, timedelta

import pytest
from prometheus_client import REGISTRY
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.models.auditoria import AuditLog
from app.models.recomendacao import Evidencia, Recomendacao


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _violadas(regra):
    return REGISTRY.get_sample_value("itam_regras_violadas_total", {"regra": regra}) or 0.0


def _total(db, modelo):
    return db.scalar(select(func.count()).select_from(modelo))


def _corpo(responsavel, **sobrescritas):
    corpo = {
        "titulo": "Renovar o contrato do pacote de escritório",
        "contexto": "A licença vence em 20 dias e o uso está em 96% do contratado.",
        "recomendacao": "Renovar com o quantitativo atual.",
        "responsavel_id": responsavel.id,
        "evidencias": [{"tipo": "PREMISSA", "descricao": "Orçamento aprovado para 2026"}],
        **sobrescritas,
    }
    return {k: v for k, v in corpo.items() if v is not ...}


def _registrar(client, token, corpo):
    return client.post("/api/v1/recomendacoes", headers=_headers(token), json=corpo)


def test_ac051_recomendacao_sem_evidencia_e_recusada_com_a_regra_na_auditoria_e_na_metrica(
    client, db, token_admin, responsavel
):
    antes = _violadas("BR-027")

    resposta = _registrar(client, token_admin, _corpo(responsavel, evidencias=[]))

    assert resposta.status_code == 409
    corpo = resposta.json()
    assert corpo["regra"] == "BR-027"
    assert "evidência" in corpo["detalhe"]  # mensagem explícita
    assert _total(db, Recomendacao) == 0 and _total(db, Evidencia) == 0
    recusas = db.scalars(select(AuditLog).where(AuditLog.resultado == "RECUSADO")).all()
    assert [(a.entidade, a.operacao, a.regra_violada) for a in recusas] == [
        ("recomendacao", "CRIAR", "BR-027")
    ]
    assert _violadas("BR-027") == antes + 1


def test_ac051_omitir_o_campo_evidencias_tambem_e_recusado(client, db, token_admin, responsavel):
    resposta = _registrar(client, token_admin, _corpo(responsavel, evidencias=...))

    assert resposta.status_code == 409 and resposta.json()["regra"] == "BR-027"
    assert _total(db, Recomendacao) == 0


def test_com_uma_evidencia_a_recomendacao_e_gravada_junto_com_ela(
    client, db, token_admin, responsavel
):
    resposta = _registrar(client, token_admin, _corpo(responsavel))

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["status"] == "PROPOSTA" and corpo["data_source"] == "manual"
    assert corpo["data"] == date.today().isoformat() and corpo["responsavel_id"] == responsavel.id
    assert [(e["tipo"], e["referencia_id"], e["descricao"]) for e in corpo["evidencias"]] == [
        ("PREMISSA", None, "Orçamento aprovado para 2026")
    ]
    assert _total(db, Recomendacao) == 1 and _total(db, Evidencia) == 1


def test_evidencias_dos_sete_tipos_apontam_para_o_que_existe(
    client, db, token_admin, responsavel, novo_ativo, nova_licenca, fornecedor
):
    risco = client.post(
        "/api/v1/riscos",
        headers=_headers(token_admin),
        json={
            "titulo": "Risco de teste",
            "categoria": "LEGAL",
            "probabilidade": 3,
            "impacto": 3,
            "resposta": "MITIGAR",
        },
    ).json()["id"]
    ativo, licenca = novo_ativo(), nova_licenca()
    scorecard = client.post(
        "/api/v1/fornecedores/scorecard",
        headers=_headers(token_admin),
        json={
            "periodo": "2026-T3",
            "criterios": [{"nome": "preco", "peso": "100"}],
            "avaliacoes": [{"fornecedor_id": fornecedor.id, "notas": {"preco": "8"}}],
        },
    )
    assert scorecard.status_code == 201
    evidencias = [
        {"tipo": "INDICADOR", "descricao": "KPI-03 conformidade de licenças = 66,67%"},
        {"tipo": "RISCO", "referencia_id": risco},
        {"tipo": "ATIVO", "referencia_id": ativo},
        {"tipo": "LICENCA", "referencia_id": licenca, "descricao": "vence em 20 dias"},
        {"tipo": "SCORECARD", "referencia_id": fornecedor.id},
        {"tipo": "CENARIO", "descricao": "RENOVAR: TCO 400.000,00 contra 420.000,00 de MANTER"},
        {"tipo": "PREMISSA", "descricao": "Reajuste de 5% ao ano"},
    ]

    resposta = _registrar(client, token_admin, _corpo(responsavel, evidencias=evidencias))

    assert resposta.status_code == 201, resposta.text
    assert [(e["tipo"], e["referencia_id"]) for e in resposta.json()["evidencias"]] == [
        ("INDICADOR", None),
        ("RISCO", risco),
        ("ATIVO", ativo),
        ("LICENCA", licenca),
        ("SCORECARD", fornecedor.id),
        ("CENARIO", None),
        ("PREMISSA", None),
    ]
    assert _total(db, Evidencia) == 7


@pytest.mark.parametrize(
    ("evidencia", "recurso"),
    [
        ({"tipo": "RISCO", "referencia_id": 999}, "Risco 999"),
        ({"tipo": "ATIVO", "referencia_id": 999}, "Ativo 999"),
        ({"tipo": "LICENCA", "referencia_id": 999}, "Licença 999"),
        ({"tipo": "SCORECARD", "referencia_id": 999}, "Fornecedor com scorecard 999"),
    ],
)
def test_evidencia_que_aponta_para_o_que_nao_existe_e_404_e_nada_e_gravado(
    client, db, token_admin, responsavel, evidencia, recurso
):
    valida = {"tipo": "PREMISSA", "descricao": "Premissa válida"}

    resposta = _registrar(client, token_admin, _corpo(responsavel, evidencias=[valida, evidencia]))

    assert resposta.status_code == 404 and recurso in resposta.json()["detalhe"]
    assert _total(db, Recomendacao) == 0 and _total(db, Evidencia) == 0  # a válida não fica sozinha


def test_scorecard_so_vale_para_fornecedor_com_avaliacao(
    client, token_admin, responsavel, fornecedor
):
    resposta = _registrar(
        client,
        token_admin,
        _corpo(responsavel, evidencias=[{"tipo": "SCORECARD", "referencia_id": fornecedor.id}]),
    )

    assert resposta.status_code == 404  # o fornecedor existe, mas nunca foi avaliado


def test_responsavel_inexistente_e_404(client, db, token_admin, responsavel):
    corpo = _corpo(responsavel)
    corpo["responsavel_id"] = 9999

    assert _registrar(client, token_admin, corpo).status_code == 404
    assert _total(db, Recomendacao) == 0


@pytest.mark.parametrize(
    "evidencia",
    [
        {"tipo": "RISCO"},  # falta a referência
        {"tipo": "ATIVO", "referencia_id": 0},
        {"tipo": "INDICADOR"},  # falta a descrição
        {"tipo": "CENARIO", "descricao": "  "},
        {"tipo": "PREMISSA", "descricao": "ab"},
        {"tipo": "PREMISSA", "referencia_id": 5, "descricao": "premissa com referência"},
        {"tipo": "ALERTA", "referencia_id": 1},  # não existe no enum
        {"referencia_id": 1},
    ],
)
def test_evidencia_malformada_e_422(client, db, token_admin, responsavel, evidencia):
    resposta = _registrar(client, token_admin, _corpo(responsavel, evidencias=[evidencia]))

    assert resposta.status_code == 422
    assert _total(db, Recomendacao) == 0


@pytest.mark.parametrize(
    "ajuste",
    [
        {"titulo": "ab"},
        {"contexto": ""},
        {"recomendacao": ""},
        {"status": "ENVIADA"},
        {"data": (date.today() + timedelta(days=1)).isoformat()},
        {"responsavel_id": ...},
        {"titulo": ...},
    ],
)
def test_corpo_invalido_e_422(client, token_admin, responsavel, ajuste):
    assert _registrar(client, token_admin, _corpo(responsavel, **ajuste)).status_code == 422


def test_a_decisao_e_humana_status_e_data_vem_de_quem_registra(client, token_admin, responsavel):
    corpo = _registrar(
        client,
        token_admin,
        _corpo(
            responsavel,
            status="APROVADA",
            data="2026-03-20",
            alternativas="Migrar para assinatura; manter o contrato atual.",
        ),
    ).json()

    assert corpo["status"] == "APROVADA" and corpo["data"] == "2026-03-20"
    assert corpo["alternativas"] == "Migrar para assinatura; manter o contrato atual."


def test_o_sistema_nao_gera_recomendacao_sozinho(client, db, token_admin):
    client.get("/api/v1/compliance/alertas", headers=_headers(token_admin))
    client.get("/api/v1/indicadores", headers=_headers(token_admin))

    assert _total(db, Recomendacao) == 0
    lista = client.get("/api/v1/recomendacoes", headers=_headers(token_admin)).json()
    assert lista["itens"] == [] and lista["total"] == 0


def test_get_devolve_a_recomendacao_com_as_evidencias_e_404_quando_nao_existe(
    client, token_admin, responsavel
):
    criada = _registrar(client, token_admin, _corpo(responsavel)).json()

    detalhe = client.get(f"/api/v1/recomendacoes/{criada['id']}", headers=_headers(token_admin))

    assert detalhe.status_code == 200 and detalhe.json() == criada
    assert client.get("/api/v1/recomendacoes/999", headers=_headers(token_admin)).status_code == 404


def test_listagem_pagina_filtra_por_status_e_traz_as_mais_novas_primeiro(
    client, token_admin, responsavel
):
    primeira = _registrar(client, token_admin, _corpo(responsavel, titulo="Primeira")).json()
    segunda = _registrar(
        client, token_admin, _corpo(responsavel, titulo="Segunda", status="REJEITADA")
    ).json()
    terceira = _registrar(client, token_admin, _corpo(responsavel, titulo="Terceira")).json()

    def ids(**params):
        corpo = client.get(
            "/api/v1/recomendacoes", headers=_headers(token_admin), params=params
        ).json()
        return [r["id"] for r in corpo["itens"]], corpo

    todas, corpo = ids()
    assert todas == [terceira["id"], segunda["id"], primeira["id"]]
    assert (corpo["total"], corpo["pagina"], corpo["total_paginas"]) == (3, 1, 1)
    assert ids(status="REJEITADA")[0] == [segunda["id"]]
    pagina2, corpo2 = ids(tamanho=2, pagina=2)
    assert pagina2 == [primeira["id"]] and corpo2["total_paginas"] == 2
    assert all(r["evidencias"] for r in corpo["itens"])


def test_ac057_criacao_gera_auditoria_com_as_evidencias(client, db, token_admin, responsavel):
    criada = _registrar(client, token_admin, _corpo(responsavel)).json()

    auditoria = db.scalars(select(AuditLog).where(AuditLog.entidade == "recomendacao")).all()

    assert [(a.operacao, a.entidade_id, a.resultado) for a in auditoria] == [
        ("CRIAR", criada["id"], "SUCESSO")
    ]
    assert auditoria[0].detalhe == {"evidencias": [{"tipo": "PREMISSA", "referencia_id": None}]}


def test_gestor_registra_e_operador_e_auditor_nao_mas_todos_leem(
    client, token_gestor, token_operador, token_auditor, responsavel
):
    assert _registrar(client, token_gestor, _corpo(responsavel)).status_code == 201
    assert _registrar(client, token_operador, _corpo(responsavel)).status_code == 403
    assert _registrar(client, token_auditor, _corpo(responsavel)).status_code == 403
    assert client.get("/api/v1/recomendacoes/1", headers=_headers(token_auditor)).status_code == 200
    assert client.get("/api/v1/recomendacoes", headers=_headers(token_operador)).status_code == 200


def test_banco_exige_referencia_ou_descricao_conforme_o_tipo_e_apaga_em_cascata(
    client, db, token_admin, responsavel
):
    rec = _registrar(client, token_admin, _corpo(responsavel)).json()["id"]

    with pytest.raises(IntegrityError, match="ck_evidencia_referencia"):
        db.execute(
            text("INSERT INTO evidencia (recomendacao_id, tipo) VALUES (:r, 'RISCO')"), {"r": rec}
        )
    db.rollback()
    with pytest.raises(IntegrityError, match="ck_evidencia_descricao"):
        db.execute(
            text("INSERT INTO evidencia (recomendacao_id, tipo) VALUES (:r, 'CENARIO')"), {"r": rec}
        )
    db.rollback()
    with pytest.raises(IntegrityError, match="ck_evidencia_tipo"):
        db.execute(
            text(
                "INSERT INTO evidencia (recomendacao_id, tipo, referencia_id) VALUES (:r, 'X', 1)"
            ),
            {"r": rec},
        )
    db.rollback()
    db.execute(text("DELETE FROM recomendacao WHERE id = :r"), {"r": rec})
    db.commit()
    assert _total(db, Evidencia) == 0  # ON DELETE CASCADE
