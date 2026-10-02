"""Imutabilidade do histórico no banco (AC-013, BR-011, BR-025, ADR-005) e BR-007.

Roda contra o PostgreSQL de teste migrado pelo `conftest.py` (`alembic upgrade head`). Tudo roda
numa transação desfeita no final.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError

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


def _inserir(conn, sql, **params):
    return conn.execute(text(sql + " RETURNING id"), params).scalar_one()


@pytest.fixture
def vinculo(conexao):
    usuario = _inserir(
        conexao,
        "INSERT INTO usuario (login, senha_hash, nome, perfil, ativo) "
        "VALUES ('pg_trigger', 'x', 'PG', 'ADMIN', true)",
    )
    categoria = _inserir(
        conexao,
        "INSERT INTO categoria (nome, vida_util_meses, tipo_aplicavel, ativa) "
        "VALUES ('Cat PG', 60, 'HARDWARE', true)",
    )
    fornecedor = _inserir(
        conexao,
        "INSERT INTO fornecedor (razao_social, ativo, data_source) "
        "VALUES ('F PG', true, 'sintetico')",
    )
    setor = _inserir(conexao, "INSERT INTO setor (nome, ativo) VALUES ('Setor PG', true)")
    responsavel = _inserir(
        conexao,
        "INSERT INTO responsavel (nome, setor_id, ativo, data_source) "
        "VALUES ('Resp PG', :s, true, 'sintetico')",
        s=setor,
    )
    ativo = _inserir(
        conexao,
        "INSERT INTO ativo (nome, tipo, categoria_id, fornecedor_id, numero_serie, data_aquisicao,"
        " valor_compra, vida_util_meses, status, data_source) VALUES ('Ativo PG', 'HARDWARE', :c,"
        " :f, 'SN-PG', '2025-01-10', 1000, 60, 'ATIVO', 'importacao')",
        c=categoria,
        f=fornecedor,
    )
    ids = {"ativo": ativo, "responsavel": responsavel, "setor": setor, "usuario": usuario}
    ids["id"] = _novo_vinculo(conexao, ids, "2025-02-01")
    return ids


def _novo_vinculo(conn, ids, inicio):
    return _inserir(
        conn,
        "INSERT INTO historico_transferencia (ativo_id, responsavel_id, setor_id, data_inicio,"
        " registrado_por_id, data_source) VALUES (:a, :r, :s, :i, :u, 'sintetico')",
        a=ids["ativo"],
        r=ids["responsavel"],
        s=ids["setor"],
        i=inicio,
        u=ids["usuario"],
    )


def _falha(conn, sql, mensagem, **params):
    with pytest.raises(DBAPIError, match=mensagem):
        with conn.begin_nested():
            conn.execute(text(sql), params)


def test_ac013_vinculo_encerrado_nao_admite_edicao_nem_exclusao(conexao, vinculo):
    conexao.execute(
        text("UPDATE historico_transferencia SET data_fim = '2025-03-01' WHERE id = :id"),
        {"id": vinculo["id"]},
    )

    _falha(
        conexao,
        "UPDATE historico_transferencia SET data_fim = '2025-04-01' WHERE id = :id",
        "BR-011",
        id=vinculo["id"],
    )
    _falha(
        conexao,
        "UPDATE historico_transferencia SET motivo = 'x' WHERE id = :id",
        "BR-011",
        id=vinculo["id"],
    )
    _falha(
        conexao, "DELETE FROM historico_transferencia WHERE id = :id", "BR-025", id=vinculo["id"]
    )


def test_ac013_vinculo_aberto_so_admite_preencher_data_fim(conexao, vinculo):
    for coluna, valor in [
        ("data_inicio", "'2025-02-02'"),
        ("motivo", "'editado'"),
        ("data_source", "'manual'"),
        ("criado_em", "criado_em - interval '1 day'"),
        ("responsavel_id", "responsavel_id"),  # sem mudança: permitido
    ]:
        sql = f"UPDATE historico_transferencia SET {coluna} = {valor} WHERE id = :id"  # nosec B608
        if coluna == "responsavel_id":
            conexao.execute(text(sql), {"id": vinculo["id"]})
        else:
            _falha(conexao, sql, "Somente data_fim", id=vinculo["id"])

    _falha(
        conexao, "DELETE FROM historico_transferencia WHERE id = :id", "BR-025", id=vinculo["id"]
    )


def test_br007_indice_parcial_impede_segundo_vinculo_aberto(conexao, vinculo):
    with pytest.raises(IntegrityError, match="ux_vinculo_aberto"):
        with conexao.begin_nested():
            _novo_vinculo(conexao, vinculo, "2025-03-01")

    conexao.execute(
        text("UPDATE historico_transferencia SET data_fim = '2025-03-01' WHERE id = :id"),
        {"id": vinculo["id"]},
    )
    assert _novo_vinculo(conexao, vinculo, "2025-03-01")
