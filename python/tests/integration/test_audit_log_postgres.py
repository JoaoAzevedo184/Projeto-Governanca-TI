"""Imutabilidade da trilha de auditoria no banco (NFR-AUD-01, ADR-005).

Roda contra o PostgreSQL de teste migrado pelo `conftest.py` (`alembic upgrade head`). Tudo roda
numa transação desfeita no final. O `conftest.py` limpa o banco com TRUNCATE, que não aciona
trigger de linha: a limpeza entre testes não depende de DELETE em `audit_log`.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.core.config import get_settings

URL = get_settings().database_url


@pytest.fixture
def conexao():
    engine = create_engine(URL)
    with engine.connect() as conn:
        transacao = conn.begin()
        yield conn
        transacao.rollback()
    engine.dispose()


@pytest.fixture
def registro(conexao) -> int:
    return conexao.execute(
        text(
            "INSERT INTO audit_log (operacao, entidade, entidade_id, resultado) "
            "VALUES ('CRIAR', 'ativo', 1, 'SUCESSO') RETURNING id"
        )
    ).scalar_one()


def _falha(conn, sql, **params):
    with pytest.raises(DBAPIError, match="NFR-AUD-01"):
        with conn.begin_nested():
            conn.execute(text(sql), params)


def test_nfr_aud_01_audit_log_admite_insert(conexao, registro):
    assert registro


def test_nfr_aud_01_audit_log_recusa_update_e_delete(conexao, registro):
    _falha(conexao, "UPDATE audit_log SET resultado = 'RECUSADO' WHERE id = :id", id=registro)
    _falha(conexao, "UPDATE audit_log SET operacao = operacao WHERE id = :id", id=registro)
    _falha(conexao, "DELETE FROM audit_log WHERE id = :id", id=registro)
    _falha(conexao, "DELETE FROM audit_log")

    linhas = conexao.execute(
        text("SELECT resultado FROM audit_log WHERE id = :id"), {"id": registro}
    )
    assert linhas.scalar_one() == "SUCESSO"
