"""Baixa no PostgreSQL: o que o banco garante (BR-024, BR-025, NFR-AUD-01) e a concorrência.

Roda contra o PostgreSQL de teste migrado pelo `conftest.py` (`alembic upgrade head`). Os testes
de garantia usam uma transação desfeita no final; os de concorrência usam conexões reais, sem mock.
"""

import threading
import time

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.core.config import get_settings
from app.core.database import engine

URL = get_settings().database_url
BAIXA_SQL = (
    "INSERT INTO baixa_ativo (ativo_id, motivo, justificativa, data_baixa, destinacao,"
    " valor_residual_baixa, registrado_por_id, data_source)"
    " VALUES (:a, :m, :j, '2025-07-10', 'DESCARTE', :r, :u, 'manual') RETURNING id"
)


@pytest.fixture
def conexao():
    motor = create_engine(URL)
    with motor.connect() as conn:
        transacao = conn.begin()
        yield conn
        transacao.rollback()
    motor.dispose()


def _inserir(conn, sql, **params):
    return conn.execute(text(sql + " RETURNING id"), params).scalar_one()


@pytest.fixture
def ids(conexao):
    usuario = _inserir(
        conexao,
        "INSERT INTO usuario (login, senha_hash, nome, perfil, ativo)"
        " VALUES ('pg_baixa', 'x', 'PG', 'ADMIN', true)",
    )
    categoria = _inserir(
        conexao,
        "INSERT INTO categoria (nome, vida_util_meses, tipo_aplicavel, ativa)"
        " VALUES ('Cat PG', 60, 'HARDWARE', true)",
    )
    fornecedor = _inserir(
        conexao,
        "INSERT INTO fornecedor (razao_social, ativo, data_source) VALUES ('F PG', true, 'manual')",
    )
    ativo = _inserir(
        conexao,
        "INSERT INTO ativo (nome, tipo, categoria_id, fornecedor_id, numero_serie, data_aquisicao,"
        " valor_compra, vida_util_meses, status, data_source) VALUES ('Ativo PG', 'HARDWARE', :c,"
        " :f, 'SN-PG-BAIXA', '2025-01-10', 1000, 60, 'ATIVO', 'manual')",
        c=categoria,
        f=fornecedor,
    )
    return {"usuario": usuario, "ativo": ativo}


def _baixa(conn, ids, motivo="DEFEITO", justificativa=None, residual=900):
    return conn.execute(
        text(BAIXA_SQL),
        {"a": ids["ativo"], "m": motivo, "j": justificativa, "r": residual, "u": ids["usuario"]},
    ).scalar_one()


def _falha(conn, excecao, mensagem, sql, **params):
    with pytest.raises(excecao, match=mensagem):
        with conn.begin_nested():
            conn.execute(text(sql), params)


def test_nfr_aud_01_baixa_admite_insert_e_recusa_update_e_delete(conexao, ids):
    baixa = _baixa(conexao, ids)

    assert baixa
    _falha(
        conexao,
        DBAPIError,
        "NFR-AUD-01",
        "UPDATE baixa_ativo SET motivo = 'OUTRO' WHERE id = :i",
        i=baixa,
    )
    _falha(
        conexao,
        DBAPIError,
        "NFR-AUD-01",
        "UPDATE baixa_ativo SET motivo = motivo WHERE id = :i",
        i=baixa,
    )
    _falha(conexao, DBAPIError, "NFR-AUD-01", "DELETE FROM baixa_ativo WHERE id = :i", i=baixa)
    _falha(conexao, DBAPIError, "NFR-AUD-01", "DELETE FROM baixa_ativo")


def test_br024_unique_impede_segunda_baixa_do_mesmo_ativo(conexao, ids):
    _baixa(conexao, ids)

    with pytest.raises(IntegrityError, match="baixa_ativo_ativo_id_key"):
        with conexao.begin_nested():
            _baixa(conexao, ids, motivo="OBSOLESCENCIA")


@pytest.mark.parametrize(
    "kwargs,restricao",
    [
        ({"motivo": "OUTRO", "justificativa": None}, "ck_baixa_justificativa"),
        ({"motivo": "OUTRO", "justificativa": "curta"}, "ck_baixa_justificativa"),
        ({"motivo": "INVENTADO"}, "ck_baixa_motivo"),
        ({"residual": -0.01}, "ck_baixa_residual_nao_negativo"),
    ],
)
def test_checks_de_baixa_ativo_sao_do_banco(conexao, ids, kwargs, restricao):
    with pytest.raises(IntegrityError, match=restricao):
        with conexao.begin_nested():
            _baixa(conexao, ids, **kwargs)


def test_check_de_destinacao_e_do_banco(conexao, ids):
    with pytest.raises(IntegrityError, match="ck_baixa_destinacao"):
        with conexao.begin_nested():
            conexao.execute(
                text(BAIXA_SQL.replace("'DESCARTE'", "'JOGAR_FORA'")),
                {"a": ids["ativo"], "m": "DEFEITO", "j": None, "r": 1, "u": ids["usuario"]},
            )


# ------------------------------------------------------------------ concorrência (conexões reais)


@pytest.fixture
def ativo_id(client, token_admin, categoria, fornecedor):
    resposta = client.post(
        "/api/v1/ativos",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "nome": "Notebook Concorrencia",
            "tipo": "HARDWARE",
            "categoria_id": categoria.id,
            "fornecedor_id": fornecedor.id,
            "numero_serie": "SN-CONC-BAIXA",
            "data_aquisicao": "2025-01-10",
            "valor_compra": "6000.00",
        },
    )
    return resposta.json()["id"]


CORPO = {"motivo": "DEFEITO", "data_baixa": "2025-07-10", "destinacao": "DESCARTE"}


def _monitor():
    # AUTOCOMMIT: pg_stat_activity é congelada por transação; sem isso o polling nunca vê mudança.
    return engine.connect().execution_options(isolation_level="AUTOCOMMIT")


def _esperar_bloqueio(pid):
    with _monitor() as monitor:
        consulta = text(
            "SELECT count(*) FROM pg_stat_activity WHERE :pid = ANY(pg_blocking_pids(pid))"
        )
        limite = time.monotonic() + 10
        while not monitor.scalar(consulta, {"pid": pid}):
            assert time.monotonic() < limite, "a baixa não bloqueou"
            time.sleep(0.02)  # polling da condição, não sincronização por tempo


def test_br024_duas_baixas_simultaneas_uma_vence_e_a_outra_grava_recusa(
    client, db, token_admin, ativo_id
):
    """Duas baixas disputam o mesmo ativo: o lock da linha as serializa. Uma conexão externa
    segura o lock; as duas requisições bloqueiam nele e, ao soltá-lo, só uma baixa (201), e a
    outra recebe 409 BR-024 com a recusa na auditoria."""
    from fastapi.testclient import TestClient

    from app.main import app

    app.dependency_overrides.clear()  # cada requisição usa a própria sessão e conexão
    segurando = engine.connect()
    transacao = segurando.begin()
    segurando.execute(text("SELECT id FROM ativo WHERE id = :i FOR UPDATE"), {"i": ativo_id})

    respostas = []
    cabecalho = {"Authorization": f"Bearer {token_admin}"}

    def baixar():
        with TestClient(app) as cliente:
            respostas.append(
                cliente.post(f"/api/v1/ativos/{ativo_id}/baixa", headers=cabecalho, json=CORPO)
            )

    threads = [threading.Thread(target=baixar) for _ in range(2)]
    for thread in threads:
        thread.start()
    try:
        with _monitor() as monitor:
            # A 2ª baixa espera na 1ª (fila do lock de linha), não na conexão que segura: conta
            # as sessões bloqueadas por alguém, e a que segura não está entre elas.
            consulta = text(
                "SELECT count(*) FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0"
            )
            limite = time.monotonic() + 10
            while monitor.scalar(consulta) < 2:
                assert time.monotonic() < limite, "as duas baixas não bloquearam no ativo"
                time.sleep(0.02)
        transacao.commit()
    finally:
        segurando.close()
        for thread in threads:
            thread.join(timeout=10)
    assert not any(thread.is_alive() for thread in threads)

    assert sorted(r.status_code for r in respostas) == [201, 409]
    recusada = next(r for r in respostas if r.status_code == 409)
    assert recusada.json()["regra"] == "BR-024"
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT count(*) FROM baixa_ativo")) == 1
        assert (
            conn.scalar(text("SELECT status FROM ativo WHERE id = :i"), {"i": ativo_id})
            == "BAIXADO"
        )
        recusas = conn.execute(
            text("SELECT regra_violada FROM audit_log WHERE resultado = 'RECUSADO'")
        ).all()
    assert recusas == [("BR-024",)]


def test_br024_conflito_real_no_unique_grava_recusa_na_auditoria(client, db, token_admin, ativo_id):
    """O UNIQUE é a garantia de BR-024. Pela API o lock no ativo serializa as baixas; só um
    escritor externo que insira direto em baixa_ativo o provoca. Aqui ele é uma segunda conexão
    real que insere sem confirmar; a baixa pela API bloqueia no índice e, quando a conexão
    externa confirma, recebe o IntegrityError real (NFR-AUD-05)."""
    registrado_por = db.scalar(text("SELECT id FROM usuario WHERE login = 'admin_teste'"))
    externo = engine.connect()
    transacao_externa = externo.begin()
    pid_externo = externo.scalar(text("SELECT pg_backend_pid()"))
    externo.execute(
        text(BAIXA_SQL),
        {"a": ativo_id, "m": "DEFEITO", "j": None, "r": 1, "u": registrado_por},
    )

    resultado = {}

    def baixar():
        resultado["resposta"] = client.post(
            f"/api/v1/ativos/{ativo_id}/baixa",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=CORPO,
        )

    thread = threading.Thread(target=baixar)
    thread.start()
    try:
        _esperar_bloqueio(pid_externo)
        transacao_externa.commit()
    finally:
        externo.close()
        thread.join(timeout=10)
    assert not thread.is_alive()

    resposta = resultado["resposta"]
    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-024"
    with engine.connect() as conn:
        auditoria = conn.execute(
            text(
                "SELECT operacao, resultado, regra_violada FROM audit_log"
                " WHERE entidade = 'baixa_ativo'"
            )
        ).all()
        status = conn.scalar(text("SELECT status FROM ativo WHERE id = :i"), {"i": ativo_id})
        baixas = conn.scalar(text("SELECT count(*) FROM baixa_ativo"))
    assert auditoria == [("CRIAR", "RECUSADO", "BR-024")]
    assert status == "ATIVO"  # nada da baixa pela API ficou
    assert baixas == 1  # só a do escritor externo
