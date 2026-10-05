"""Chave de licença única no PostgreSQL (BR-039, AC-067): o índice e a corrida real.

Roda contra o PostgreSQL de teste migrado pelo `conftest.py`. O conflito é provocado com uma
segunda conexão real, sem mock (docs/guia/testes.md).
"""

import threading
import time

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import engine

CHAVE = "RACE-1111-2222-ABCD"
INSERIR_ATIVO = text(
    "INSERT INTO ativo (nome, tipo, categoria_id, fornecedor_id, chave_licenca, data_aquisicao,"
    " valor_compra, vida_util_meses, status, data_source) VALUES ('Suite Externa', 'SOFTWARE',"
    " :c, :f, :k, '2025-01-10', 100, 36, 'ATIVO', 'sintetico')"
)


def test_indice_unico_e_parcial_so_para_chave_nao_nula(db):
    indice = db.execute(
        text("SELECT indexdef FROM pg_indexes WHERE indexname = 'ux_ativo_chave_licenca'")
    ).scalar_one()

    assert "UNIQUE" in indice
    assert "WHERE (chave_licenca IS NOT NULL)" in indice


def test_licenca_continua_sem_unicidade_na_chave(db):
    """Decisão da equipe (2026-10-05): a renovação de subscrição pode repetir a chave."""
    indices = db.execute(
        text(
            "SELECT indexdef FROM pg_indexes WHERE tablename = 'licenca'"
            " AND indexdef LIKE '%UNIQUE%' AND indexdef LIKE '%chave_licenca%'"
        )
    ).all()
    restricoes = db.execute(
        text(
            "SELECT conname FROM pg_constraint WHERE conrelid = 'licenca'::regclass"
            " AND contype = 'u'"
        )
    ).all()

    assert indices == [] and restricoes == []


def _cadastrar_com_escritor_externo(client, token, categoria, fornecedor, externo_sql, payload):
    """Corrida real: um escritor externo (ETL, carga D.8) insere sem confirmar; o cadastro passa
    pelas checagens do serviço, bloqueia no índice único e recebe o IntegrityError quando o
    externo confirma. Devolve a resposta do cadastro ou, se o
    erro subir sem tratamento, a exceção (chave `erro`)."""
    externo = engine.connect()
    transacao_externa = externo.begin()
    pid_externo = externo.scalar(text("SELECT pg_backend_pid()"))
    externo.execute(externo_sql, {"c": categoria.id, "f": fornecedor.id})

    resultado = {}

    def cadastrar():
        try:
            resultado["resposta"] = client.post(
                "/api/v1/ativos", headers={"Authorization": f"Bearer {token}"}, json=payload
            )
        except Exception as erro:  # o TestClient repropaga o erro não tratado do servidor
            resultado["erro"] = erro

    thread = threading.Thread(target=cadastrar)
    thread.start()
    try:
        # AUTOCOMMIT: pg_stat_activity é congelada por transação; sem isso o polling não atualiza.
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as monitor:
            consulta = text(
                "SELECT count(*) FROM pg_stat_activity WHERE :pid = ANY(pg_blocking_pids(pid))"
            )
            limite = time.monotonic() + 10
            while not monitor.scalar(consulta, {"pid": pid_externo}):
                assert time.monotonic() < limite, "o cadastro não bloqueou no índice"
                time.sleep(0.02)  # polling da condição, não sincronização por tempo
        transacao_externa.commit()
    finally:
        externo.close()
        thread.join(timeout=10)
    assert not thread.is_alive()
    return resultado


def _payload(categoria, fornecedor, **campos):
    return {
        "nome": "Ativo Concorrente",
        "tipo": "SOFTWARE",
        "categoria_id": categoria.id,
        "fornecedor_id": fornecedor.id,
        "data_aquisicao": "2025-01-10",
        "valor_compra": "100.00",
        **campos,
    }


def test_ac067_conflito_real_no_indice_grava_recusa_na_auditoria(
    client, db, token_admin, categoria, fornecedor
):
    """NFR-AUD-05 com a corrida provocada de verdade, sem mock."""
    resposta = _cadastrar_com_escritor_externo(
        client,
        token_admin,
        categoria,
        fornecedor,
        INSERIR_ATIVO.bindparams(k=CHAVE),
        _payload(categoria, fornecedor, chave_licenca=CHAVE),
    )["resposta"]

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-039"
    assert CHAVE not in resposta.text
    with engine.connect() as conexao:
        auditoria = conexao.execute(
            text(
                "SELECT operacao, resultado, regra_violada, detalhe FROM audit_log"
                " WHERE entidade = 'ativo'"
            )
        ).all()
        ativos = conexao.execute(text("SELECT id, nome, data_source FROM ativo")).all()
    assert len(auditoria) == 1
    operacao, resultado_auditoria, regra, detalhe = auditoria[0]
    assert (operacao, resultado_auditoria, regra) == ("CRIAR", "RECUSADO", "BR-039")
    assert CHAVE not in str(detalhe)
    assert [(a[1], a[2]) for a in ativos] == [("Suite Externa", "sintetico")]
    assert detalhe == {"ativo_conflitante_id": ativos[0][0]}  # nada do cadastro concorrente ficou


def test_corrida_em_outro_indice_nao_vira_br039(client, db, token_admin, categoria, fornecedor):
    """Só o índice da chave vira BR-039. A corrida no número de série segue como antes desta
    regra: o IntegrityError sobe sem tratamento (a API responderia 500). É uma lacuna conhecida,
    fora do escopo da BR-039; o teste fixa que a regra nova não engole o erro dos outros índices."""
    externo_sql = text(
        "INSERT INTO ativo (nome, tipo, categoria_id, fornecedor_id, numero_serie, data_aquisicao,"
        " valor_compra, vida_util_meses, status, data_source) VALUES ('Externo', 'HARDWARE',"
        " :c, :f, 'SN-CORRIDA', '2025-01-10', 100, 36, 'ATIVO', 'sintetico')"
    )

    resultado = _cadastrar_com_escritor_externo(
        client,
        token_admin,
        categoria,
        fornecedor,
        externo_sql,
        _payload(categoria, fornecedor, tipo="HARDWARE", numero_serie="SN-CORRIDA"),
    )

    assert "resposta" not in resultado
    assert isinstance(resultado["erro"], IntegrityError)
    assert resultado["erro"].orig.diag.constraint_name == "ativo_numero_serie_key"
    with engine.connect() as conexao:
        recusas = conexao.execute(
            text("SELECT regra_violada FROM audit_log WHERE resultado = 'RECUSADO'")
        ).all()
    assert recusas == []
