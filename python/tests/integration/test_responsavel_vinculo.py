"""Vinculação e transferência de responsável (FR-002, AC-009 a AC-014)."""

import threading
import time
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from app.core.database import engine
from app.models.auditoria import AuditLog
from app.models.historico import HistoricoTransferencia
from app.models.responsavel import Responsavel
from app.utils import datas

AQUISICAO = "2025-01-10"


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ativo_id(client, token_admin, categoria, fornecedor):
    payload = {
        "nome": "Notebook Vinculo",
        "tipo": "HARDWARE",
        "categoria_id": categoria.id,
        "fornecedor_id": fornecedor.id,
        "numero_serie": "SN-VINCULO",
        "data_aquisicao": AQUISICAO,
        "valor_compra": 6000.00,
    }
    resposta = client.post("/api/v1/ativos", headers=_headers(token_admin), json=payload)
    assert resposta.status_code == 201
    return resposta.json()["id"]


@pytest.fixture
def outros_responsaveis(db, setor):
    registros = [
        Responsavel(nome=f"Colaborador {n}", matricula=f"M-10{n}", setor_id=setor.id)
        for n in range(3)
    ]
    db.add_all(registros)
    db.commit()
    return [r.id for r in registros]


def _vincular(client, token, ativo_id, responsavel_id, setor_id, data_inicio, **extra):
    corpo = {
        "responsavel_id": responsavel_id,
        "setor_id": setor_id,
        "data_inicio": data_inicio,
        **extra,
    }
    return client.post(
        f"/api/v1/ativos/{ativo_id}/responsavel", headers=_headers(token), json=corpo
    )


def _recusas(db):
    return [
        (a.regra_violada, a.detalhe["ativo_id"])
        for a in db.query(AuditLog).filter(AuditLog.resultado == "RECUSADO")
    ]


def _abertos(db, ativo_id):
    return (
        db.query(HistoricoTransferencia)
        .filter(
            HistoricoTransferencia.ativo_id == ativo_id, HistoricoTransferencia.data_fim.is_(None)
        )
        .all()
    )


def test_ac009_atribui_responsavel_a_ativo_sem_vinculo(
    client, db, token_operador, ativo_id, responsavel, setor
):
    resposta = _vincular(
        client, token_operador, ativo_id, responsavel.id, setor.id, "2025-02-01", motivo="Entrega"
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["ativo_id"] == ativo_id
    assert corpo["responsavel_id"] == responsavel.id
    assert corpo["data_inicio"] == "2025-02-01"
    assert corpo["data_fim"] is None
    assert corpo["motivo"] == "Entrega"
    assert [v.data_source for v in _abertos(db, ativo_id)] == ["manual"]


def test_ac010_transferencia_encerra_anterior_com_data_fim_igual_ao_novo_inicio(
    client, db, token_admin, ativo_id, responsavel, setor, outros_responsaveis
):
    primeiro = _vincular(client, token_admin, ativo_id, responsavel.id, setor.id, "2025-02-01")
    novo = _vincular(client, token_admin, ativo_id, outros_responsaveis[0], setor.id, "2025-06-15")

    assert novo.status_code == 201
    anterior = db.get(HistoricoTransferencia, primeiro.json()["id"])
    db.refresh(anterior)
    assert anterior.data_fim == date(2025, 6, 15)
    abertos = _abertos(db, ativo_id)
    assert [v.id for v in abertos] == [novo.json()["id"]]

    operacoes = {
        (a.operacao, a.entidade_id)
        for a in db.query(AuditLog).filter(AuditLog.entidade == "historico_transferencia")
    }
    assert ("ATUALIZAR", anterior.id) in operacoes
    assert ("CRIAR", novo.json()["id"]) in operacoes


def test_ac011_ativo_baixado_nao_recebe_responsavel(
    client, db, token_admin, ativo_id, responsavel, setor
):
    baixa = client.post(
        f"/api/v1/ativos/{ativo_id}/baixa",
        headers=_headers(token_admin),
        json={"motivo": "DEFEITO", "data_baixa": "2025-02-01", "destinacao": "DESCARTE"},
    )
    assert baixa.status_code == 201

    resposta = _vincular(client, token_admin, ativo_id, responsavel.id, setor.id, "2025-02-01")

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-009"
    assert _abertos(db, ativo_id) == []
    recusa = db.query(AuditLog).filter(AuditLog.resultado == "RECUSADO").one()
    assert recusa.regra_violada == "BR-009"
    assert recusa.entidade == "historico_transferencia"


def test_ac012_tres_transferencias_retornam_quatro_vinculos_sem_sobreposicao(
    client, token_auditor, token_admin, ativo_id, responsavel, setor, outros_responsaveis
):
    inicios = ["2025-02-01", "2025-04-01", "2025-06-01", "2025-08-01"]
    for responsavel_id, inicio in zip([responsavel.id, *outros_responsaveis], inicios, strict=True):
        assert (
            _vincular(client, token_admin, ativo_id, responsavel_id, setor.id, inicio).status_code
            == 201
        )

    resposta = client.get(f"/api/v1/ativos/{ativo_id}/historico", headers=_headers(token_auditor))

    assert resposta.status_code == 200
    vinculos = resposta.json()
    assert len(vinculos) == 4
    assert [v["data_inicio"] for v in vinculos] == sorted(inicios, reverse=True)  # FR-002: desc
    assert vinculos[0]["data_fim"] is None
    cronologico = list(reversed(vinculos))
    for anterior, seguinte in zip(cronologico, cronologico[1:], strict=False):
        assert anterior["data_fim"] == seguinte["data_inicio"]


def test_historico_desempata_vinculos_do_mesmo_dia_pelo_mais_recente(
    client, token_admin, ativo_id, responsavel, setor, outros_responsaveis
):
    _vincular(client, token_admin, ativo_id, responsavel.id, setor.id, "2025-02-01")
    segundo = _vincular(
        client, token_admin, ativo_id, outros_responsaveis[0], setor.id, "2025-02-01"
    )

    vinculos = client.get(
        f"/api/v1/ativos/{ativo_id}/historico", headers=_headers(token_admin)
    ).json()

    assert vinculos[0]["id"] == segundo.json()["id"]
    assert vinculos[0]["data_fim"] is None
    assert vinculos[1]["data_fim"] == "2025-02-01"


@pytest.mark.parametrize("metodo", ["PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("perfil", ["admin", "operador", "gestor", "auditor"])
def test_ac013_nenhum_perfil_edita_ou_exclui_vinculo_pela_api(
    request, client, token_admin, ativo_id, responsavel, setor, metodo, perfil
):
    # A API não expõe edição nem exclusão de vínculo; a garantia no banco (trigger) é
    # testada contra PostgreSQL em test_historico_postgres.py.
    vinculo = _vincular(client, token_admin, ativo_id, responsavel.id, setor.id, "2025-02-01")
    token = request.getfixturevalue(f"token_{perfil}")

    for path in (
        f"/api/v1/ativos/{ativo_id}/historico",
        f"/api/v1/ativos/{ativo_id}/historico/{vinculo.json()['id']}",
        f"/api/v1/ativos/{ativo_id}/responsavel",
    ):
        resposta = client.request(metodo, path, headers=_headers(token), json={})
        assert resposta.status_code in (404, 405), f"{metodo} {path} -> {resposta.status_code}"


def test_ac014_recusa_data_inicio_anterior_a_aquisicao(
    client, db, token_admin, ativo_id, responsavel, setor
):
    resposta = _vincular(client, token_admin, ativo_id, responsavel.id, setor.id, "2025-01-09")

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-010"
    assert _abertos(db, ativo_id) == []
    assert _recusas(db) == [("BR-010", ativo_id)]


def test_aceita_data_inicio_igual_a_aquisicao(
    client, db, token_admin, ativo_id, responsavel, setor
):
    resposta = _vincular(client, token_admin, ativo_id, responsavel.id, setor.id, AQUISICAO)
    assert resposta.status_code == 201
    assert [v.data_inicio for v in _abertos(db, ativo_id)] == [date(2025, 1, 10)]


def test_recusa_transferencia_com_inicio_anterior_ao_vinculo_vigente(
    client, db, token_admin, ativo_id, responsavel, setor, outros_responsaveis
):
    primeiro = _vincular(client, token_admin, ativo_id, responsavel.id, setor.id, "2025-06-01")

    resposta = _vincular(
        client, token_admin, ativo_id, outros_responsaveis[0], setor.id, "2025-05-31"
    )

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-008"
    assert [v.id for v in _abertos(db, ativo_id)] == [primeiro.json()["id"]]
    assert _recusas(db) == [("BR-008", ativo_id)]


def test_recusa_data_inicio_futura(client, db, token_admin, ativo_id, responsavel, setor):
    amanha = (datas.hoje() + timedelta(days=1)).isoformat()
    resposta = _vincular(client, token_admin, ativo_id, responsavel.id, setor.id, amanha)
    assert resposta.status_code == 422
    assert _abertos(db, ativo_id) == []


@pytest.mark.parametrize("inativo", ["responsavel", "setor"])
def test_ac065_recusa_responsavel_ou_setor_inativo(
    client, db, token_admin, ativo_id, responsavel, setor, inativo
):
    registro = responsavel if inativo == "responsavel" else setor
    registro.ativo = False
    db.commit()

    resposta = _vincular(client, token_admin, ativo_id, responsavel.id, setor.id, "2025-02-01")

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-038"
    assert _abertos(db, ativo_id) == []
    assert _recusas(db) == [("BR-038", ativo_id)]


@pytest.mark.parametrize(
    ("alvo", "mensagem"),
    [("ativo", "Ativo 999"), ("responsavel", "Responsável 999"), ("setor", "Setor 999")],
)
def test_referencias_inexistentes_retornam_404(
    client, db, token_admin, ativo_id, responsavel, setor, alvo, mensagem
):
    ids = {"ativo": ativo_id, "responsavel": responsavel.id, "setor": setor.id, alvo: 999}

    resposta = _vincular(
        client, token_admin, ids["ativo"], ids["responsavel"], ids["setor"], "2025-02-01"
    )

    assert resposta.status_code == 404
    assert mensagem in resposta.json()["detalhe"]
    assert db.query(HistoricoTransferencia).count() == 0


def test_historico_de_ativo_inexistente_retorna_404(client, token_admin):
    resposta = client.get("/api/v1/ativos/999/historico", headers=_headers(token_admin))
    assert resposta.status_code == 404


def test_ac057_vinculo_registra_auditoria_de_criacao(
    client, db, token_admin, ativo_id, responsavel, setor
):
    resposta = _vincular(client, token_admin, ativo_id, responsavel.id, setor.id, "2025-02-01")

    registro = (
        db.query(AuditLog)
        .filter(
            AuditLog.entidade == "historico_transferencia",
            AuditLog.entidade_id == resposta.json()["id"],
        )
        .one()
    )
    assert registro.operacao == "CRIAR"
    assert registro.resultado == "SUCESSO"


def test_br007_conflito_real_no_indice_grava_recusa_na_auditoria(
    client, db, token_admin, ativo_id, responsavel, setor
):
    """NFR-AUD-05 com o conflito provocado de verdade no PostgreSQL, sem mock.

    Pela API o conflito é inalcançável: o lock no ativo serializa as transferências. Só um
    escritor externo que insere direto em historico_transferencia (ETL, carga D.8) o provoca;
    aqui ele é uma segunda conexão real. Ver docs/ROADMAP.md.
    """
    registrado_por = db.scalar(text("SELECT id FROM usuario WHERE login = 'admin_teste'"))
    externo = engine.connect()
    transacao_externa = externo.begin()
    pid_externo = externo.scalar(text("SELECT pg_backend_pid()"))
    # 1. Vínculo aberto inserido pela segunda conexão, sem confirmar.
    externo.execute(
        text(
            "INSERT INTO historico_transferencia (ativo_id, responsavel_id, setor_id, data_inicio,"
            " registrado_por_id, data_source) VALUES (:a, :r, :s, '2025-02-01', :u, 'sintetico')"
        ),
        {"a": ativo_id, "r": responsavel.id, "s": setor.id, "u": registrado_por},
    )

    # 2. A transferência roda numa thread e bloqueia no índice ux_vinculo_aberto.
    resultado = {}

    def transferir():
        resultado["resposta"] = _vincular(
            client, token_admin, ativo_id, responsavel.id, setor.id, "2025-03-01"
        )

    thread = threading.Thread(target=transferir)
    thread.start()
    try:
        # AUTOCOMMIT: pg_stat_activity é congelada por transação; sem isso o polling não atualiza.
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as monitor:
            consulta = text(
                "SELECT count(*) FROM pg_stat_activity WHERE :pid = ANY(pg_blocking_pids(pid))"
            )
            limite = time.monotonic() + 10
            while not monitor.scalar(consulta, {"pid": pid_externo}):
                assert time.monotonic() < limite, "a transferência não bloqueou no índice"
                time.sleep(0.02)  # polling da condição, não sincronização por tempo
        # 3. A segunda conexão confirma; a transferência recebe o IntegrityError real.
        transacao_externa.commit()
    finally:
        externo.close()
        thread.join(timeout=10)
    assert not thread.is_alive()

    # 4. Resposta 409 BR-007 e linha RECUSADO na auditoria, lida por conexão nova.
    resposta = resultado["resposta"]
    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-007"
    with engine.connect() as conexao:
        auditoria = conexao.execute(
            text(
                "SELECT operacao, resultado, regra_violada, detalhe FROM audit_log"
                " WHERE entidade = 'historico_transferencia'"
            )
        ).all()
        abertos = conexao.execute(
            text("SELECT data_source FROM historico_transferencia WHERE data_fim IS NULL")
        ).all()
    assert auditoria == [("CRIAR", "RECUSADO", "BR-007", {"ativo_id": ativo_id})]
    assert abertos == [("sintetico",)]  # só o vínculo externo; nada da transferência ficou
