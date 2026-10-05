"""Índices únicos de `ativo` no PostgreSQL (BR-039, AC-067; BR-001, AC-070): índice e corrida real.

Roda contra o PostgreSQL de teste migrado pelo `conftest.py`. O conflito é provocado com uma
segunda conexão real, sem mock (docs/guia/testes.md).
"""

import io
import threading
import time

from prometheus_client import REGISTRY
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


def _com_escritor_externo(externo_sql, parametros, requisicao):
    """Corrida real: um escritor externo (ETL, carga D.8) executa `externo_sql` sem confirmar; a
    `requisicao(client)` passa pelas checagens do serviço, bloqueia no banco e só prossegue quando
    o externo confirma. Devolve `{"resposta": ...}` ou, se o erro subir sem tratamento (o
    TestClient o repropaga), `{"erro": exceção}`."""
    externo = engine.connect()
    transacao_externa = externo.begin()
    pid_externo = externo.scalar(text("SELECT pg_backend_pid()"))
    externo.execute(externo_sql, parametros)

    resultado = {}

    def executar():
        try:
            resultado["resposta"] = requisicao()
        except Exception as erro:  # o TestClient repropaga o erro não tratado do servidor
            resultado["erro"] = erro

    thread = threading.Thread(target=executar)
    thread.start()
    try:
        # AUTOCOMMIT: pg_stat_activity é congelada por transação; sem isso o polling não atualiza.
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as monitor:
            consulta = text(
                "SELECT count(*) FROM pg_stat_activity WHERE :pid = ANY(pg_blocking_pids(pid))"
            )
            limite = time.monotonic() + 10
            while not monitor.scalar(consulta, {"pid": pid_externo}):
                assert time.monotonic() < limite, "a requisição não bloqueou no banco"
                time.sleep(0.02)  # polling da condição, não sincronização por tempo
        transacao_externa.commit()
    finally:
        externo.close()
        thread.join(timeout=10)
    assert not thread.is_alive()
    return resultado


def _cadastrar_com_escritor_externo(client, token, categoria, fornecedor, externo_sql, payload):
    return _com_escritor_externo(
        externo_sql,
        {"c": categoria.id, "f": fornecedor.id},
        lambda: client.post(
            "/api/v1/ativos", headers={"Authorization": f"Bearer {token}"}, json=payload
        ),
    )


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


def _violadas(regra: str) -> float:
    return REGISTRY.get_sample_value("itam_regras_violadas_total", {"regra": regra}) or 0.0


def test_ac070_corrida_real_no_numero_de_serie_recusa_com_br001_e_audita(
    client, db, token_admin, categoria, fornecedor
):
    """Mesma corrida do BR-039, agora no índice do número de série: antes subia como
    IntegrityError e a API respondia 500; agora é 409 com `regra = BR-001`."""
    externo_sql = text(
        "INSERT INTO ativo (nome, tipo, categoria_id, fornecedor_id, numero_serie, data_aquisicao,"
        " valor_compra, vida_util_meses, status, data_source) VALUES ('Externo', 'HARDWARE',"
        " :c, :f, 'SN-CORRIDA', '2025-01-10', 100, 36, 'ATIVO', 'sintetico')"
    )
    antes = _violadas("BR-001")

    resposta = _cadastrar_com_escritor_externo(
        client,
        token_admin,
        categoria,
        fornecedor,
        externo_sql,
        _payload(categoria, fornecedor, tipo="HARDWARE", numero_serie="SN-CORRIDA"),
    )["resposta"]

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-001"
    assert _violadas("BR-001") == antes + 1
    with engine.connect() as conexao:
        auditoria = conexao.execute(
            text(
                "SELECT operacao, resultado, regra_violada, detalhe FROM audit_log"
                " WHERE entidade = 'ativo'"
            )
        ).all()
        ativos = conexao.execute(text("SELECT id, nome FROM ativo")).all()
    assert auditoria == [("CRIAR", "RECUSADO", "BR-001", {"ativo_conflitante_id": ativos[0][0]})]
    assert [a[1] for a in ativos] == ["Externo"]  # nada do cadastro concorrente ficou


def test_corrida_em_outra_restricao_nao_vira_recusa_de_regra(
    client, db, token_admin, categoria, fornecedor
):
    """Só os dois índices únicos viram BR-001/BR-039. Outra restrição (aqui, a categoria apagada
    por um escritor externo entre a checagem e o INSERT: violação de FK) segue subindo como
    IntegrityError, para a regra nova não engolir erro que não é dela."""
    externo_sql = text("DELETE FROM categoria WHERE id = :c")

    resultado = _cadastrar_com_escritor_externo(
        client,
        token_admin,
        categoria,
        fornecedor,
        externo_sql,
        _payload(categoria, fornecedor, tipo="HARDWARE", numero_serie="SN-FK"),
    )

    assert "resposta" not in resultado
    assert isinstance(resultado["erro"], IntegrityError)
    assert resultado["erro"].orig.diag.constraint_name == "ativo_categoria_id_fkey"
    with engine.connect() as conexao:
        recusas = conexao.execute(
            text("SELECT regra_violada FROM audit_log WHERE resultado = 'RECUSADO'")
        ).all()
    assert recusas == []


def test_falha_do_banco_no_meio_do_lote_desfaz_ativos_lote_e_auditorias(
    client, db, token_admin, categoria, fornecedor
):
    """Falha real do banco durante o lote: um escritor externo apaga a categoria que as linhas
    usam (a checagem do importador a vê; o INSERT bloqueia e falha na FK). Nada fica: nem os
    ativos, nem o lote, nem as auditorias, porque tudo é uma transação só."""
    linhas = [
        "nome,tipo,categoria,fornecedor,numero_serie,data_aquisicao,valor_compra",
        f"Notebook 1,HARDWARE,{categoria.nome},{fornecedor.razao_social},SN-1,2025-01-10,1000.00",
        f"Notebook 2,HARDWARE,{categoria.nome},{fornecedor.razao_social},SN-2,2025-01-10,1000.00",
    ]
    conteudo = ("\n".join(linhas) + "\n").encode("utf-8")

    resultado = _com_escritor_externo(
        text("DELETE FROM categoria WHERE id = :c"),
        {"c": categoria.id},
        lambda: client.post(
            "/api/v1/importacoes",
            headers={"Authorization": f"Bearer {token_admin}"},
            files={"arquivo": ("inventario.csv", io.BytesIO(conteudo), "text/csv")},
        ),
    )

    assert "resposta" not in resultado
    assert resultado["erro"].orig.diag.constraint_name == "ativo_categoria_id_fkey"
    with engine.connect() as conexao:
        contagens = [
            conexao.scalar(text(f"SELECT count(*) FROM {tabela}"))
            for tabela in ("ativo", "lote_importacao", "erro_importacao", "audit_log")
        ]
    assert contagens == [0, 0, 0, 0]
