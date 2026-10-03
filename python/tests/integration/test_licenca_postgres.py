"""Licenças no PostgreSQL: o que o banco garante (ck_licenca_tipo, vigência, ux_licenca_ativo) e a
concorrência de BR-018. Roda contra o PostgreSQL de teste migrado pelo `conftest.py`.

Os testes de garantia usam uma transação desfeita no final; os de concorrência usam conexões
reais, sem mock.
"""

import threading
import time

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.database import engine

URL = get_settings().database_url
LICENCA_SQL = (
    "INSERT INTO licenca (tipo_licenciamento, ativo_id, software, fornecedor_id, chave_licenca,"
    " quantidade_contratada, data_inicio_vigencia, data_expiracao, valor_total, data_source)"
    " VALUES (:t, :a, :s, :f, 'K-1234-5678', :q, :i, :e, :v, 'manual') RETURNING id"
)
VINCULO_SQL = (
    "INSERT INTO licenca_vinculo (licenca_id, ativo_id, data_vinculo, ativo_vinculo, data_source)"
    " VALUES (:l, :a, '2025-03-01', :v, 'manual') RETURNING id"
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


def _ativo(conn, categoria, fornecedor, nome, tipo, **colunas):
    identificador = "numero_serie" if tipo == "HARDWARE" else "chave_licenca"
    return _inserir(
        conn,
        f"INSERT INTO ativo (nome, tipo, categoria_id, fornecedor_id, {identificador},"  # nosec B608
        " data_aquisicao, valor_compra, vida_util_meses, status, data_source) VALUES"
        " (:n, :t, :c, :f, :i, '2025-01-10', 1000, 60, 'ATIVO', 'manual')",
        n=nome,
        t=tipo,
        c=categoria,
        f=fornecedor,
        i=f"ID-{nome}",
    )


@pytest.fixture
def ids(conexao):
    categoria = _inserir(
        conexao,
        "INSERT INTO categoria (nome, vida_util_meses, tipo_aplicavel, ativa)"
        " VALUES ('Cat PG', 60, 'HARDWARE', true)",
    )
    fornecedor = _inserir(
        conexao,
        "INSERT INTO fornecedor (razao_social, ativo, data_source) VALUES ('F PG', true, 'manual')",
    )
    return {
        "fornecedor": fornecedor,
        "software": _ativo(conexao, categoria, fornecedor, "SW PG", "SOFTWARE"),
        "maquina": _ativo(conexao, categoria, fornecedor, "HW PG", "HARDWARE"),
    }


def _licenca(conn, ids, tipo="SUBSCRICAO", **sobrescritas):
    padrao = {
        "SUBSCRICAO": {"a": None, "s": "Suite", "v": 100},
        "OEM": {"a": None, "s": "Windows OEM", "v": None},
        "PERPETUA": {"a": ids["software"], "s": None, "v": None},
    }[tipo]
    parametros = {
        "t": tipo,
        "f": ids["fornecedor"],
        "q": 2,
        "i": "2025-01-01",
        "e": "2099-12-31",
        **padrao,
        **sobrescritas,
    }
    return conn.execute(text(LICENCA_SQL), parametros).scalar_one()


@pytest.mark.parametrize("tipo", ["SUBSCRICAO", "OEM", "PERPETUA"])
def test_licenca_valida_de_cada_tipo_e_aceita(conexao, ids, tipo):
    assert _licenca(conexao, ids, tipo)


@pytest.mark.parametrize(
    "tipo,sobrescritas",
    [
        ("PERPETUA", {"a": None}),
        ("PERPETUA", {"s": "Nome"}),
        ("PERPETUA", {"v": 10}),
        ("SUBSCRICAO", {"a": "ATIVO"}),
        ("SUBSCRICAO", {"s": None}),
        ("SUBSCRICAO", {"v": None}),
        ("OEM", {"v": 10}),
        ("OEM", {"s": None}),
    ],
)
def test_ck_licenca_tipo_e_do_banco(conexao, ids, tipo, sobrescritas):
    if sobrescritas.get("a") == "ATIVO":
        sobrescritas = {"a": ids["software"]}
    with pytest.raises(IntegrityError, match="ck_licenca_tipo"):
        with conexao.begin_nested():
            _licenca(conexao, ids, tipo, **sobrescritas)


@pytest.mark.parametrize(
    "sobrescritas,restricao",
    [
        ({"e": "2025-01-01"}, "ck_licenca_vigencia"),  # BR-019: igual ao início
        ({"e": "2024-12-31"}, "ck_licenca_vigencia"),
        ({"q": 0}, "ck_licenca_quantidade_minima"),
        ({"v": 0}, "ck_licenca_valor_positivo"),
        # Tipo fora do enum: o PostgreSQL aponta o primeiro CHECK violado em ordem de nome, e
        # `ck_licenca_tipo` também não reconhece o valor.
        ({"t": "DE_GRACA"}, "ck_licenca_tipo"),
    ],
)
def test_checks_de_licenca_sao_do_banco(conexao, ids, sobrescritas, restricao):
    with pytest.raises(IntegrityError, match=restricao):
        with conexao.begin_nested():
            _licenca(conexao, ids, **sobrescritas)


def test_ux_licenca_ativo_impede_segundo_vinculo_ativo_da_mesma_maquina(conexao, ids):
    licenca = _licenca(conexao, ids)
    _inserir_vinculo = lambda ativo_vinculo=True: conexao.execute(  # noqa: E731
        text(VINCULO_SQL), {"l": licenca, "a": ids["maquina"], "v": ativo_vinculo}
    ).scalar_one()
    _inserir_vinculo()

    with pytest.raises(IntegrityError, match="ux_licenca_ativo"):
        with conexao.begin_nested():
            _inserir_vinculo()

    # O índice é parcial: vínculos desfeitos (ativo_vinculo = false) não contam, e a máquina
    # pode receber a licença de novo.
    conexao.execute(
        text("UPDATE licenca_vinculo SET ativo_vinculo = false WHERE licenca_id = :l"),
        {"l": licenca},
    )
    assert _inserir_vinculo()
    assert _inserir_vinculo(ativo_vinculo=False)  # e pode haver vários desfeitos


def test_o_mesmo_ativo_pode_receber_licencas_diferentes(conexao, ids):
    primeira, segunda = _licenca(conexao, ids), _licenca(conexao, ids, "OEM")

    for licenca in (primeira, segunda):
        conexao.execute(text(VINCULO_SQL), {"l": licenca, "a": ids["maquina"], "v": True})


# ------------------------------------------------------------------ concorrência (conexões reais)


@pytest.fixture
def cenario(client, token_admin, categoria, fornecedor):
    cabecalho = {"Authorization": f"Bearer {token_admin}"}

    def ativo(nome):
        resposta = client.post(
            "/api/v1/ativos",
            headers=cabecalho,
            json={
                "nome": f"Notebook {nome}",
                "tipo": "HARDWARE",
                "categoria_id": categoria.id,
                "fornecedor_id": fornecedor.id,
                "numero_serie": f"SN-CONC-{nome}",
                "data_aquisicao": "2025-01-10",
                "valor_compra": "1000.00",
            },
        )
        return resposta.json()["id"]

    licenca = client.post(
        "/api/v1/licencas",
        headers=cabecalho,
        json={
            "tipo_licenciamento": "SUBSCRICAO",
            "software": "Suite Concorrencia",
            "fornecedor_id": fornecedor.id,
            "chave_licenca": "CONC-1234-5678",
            "quantidade_contratada": 1,
            "data_inicio_vigencia": "2025-01-01",
            "data_expiracao": "2099-12-31",
            "valor_total": "100.00",
        },
    ).json()["id"]
    return {"licenca": licenca, "maquinas": [ativo("A"), ativo("B")], "cabecalho": cabecalho}


def _monitor():
    # AUTOCOMMIT: pg_stat_activity é congelada por transação; sem isso o polling nunca vê mudança.
    return engine.connect().execution_options(isolation_level="AUTOCOMMIT")


def test_br018_dois_vinculos_simultaneos_no_ultimo_assento_so_um_vence(client, db, cenario):
    """Duas vinculações disputam o único assento: o lock na licença as serializa. Uma conexão
    externa segura o lock; as duas requisições bloqueiam nele e, ao soltá-lo, só uma vincula
    (201); a outra recebe 409 BR-018, com a recusa na auditoria e sem exceder o contratado."""
    from fastapi.testclient import TestClient

    from app.main import app

    app.dependency_overrides.clear()  # cada requisição usa a própria sessão e conexão
    segurando = engine.connect()
    transacao = segurando.begin()
    segurando.execute(
        text("SELECT id FROM licenca WHERE id = :i FOR UPDATE"), {"i": cenario["licenca"]}
    )

    respostas = []

    def vincular(maquina):
        with TestClient(app) as cliente:
            respostas.append(
                cliente.post(
                    f"/api/v1/licencas/{cenario['licenca']}/vinculos",
                    headers=cenario["cabecalho"],
                    json={"ativo_id": maquina},
                )
            )

    threads = [threading.Thread(target=vincular, args=(m,)) for m in cenario["maquinas"]]
    for thread in threads:
        thread.start()
    try:
        with _monitor() as monitor:
            # A 2ª requisição espera na 1ª (fila do lock de linha), não na conexão que segura:
            # conta as sessões bloqueadas por alguém, e a que segura não está entre elas.
            consulta = text(
                "SELECT count(*) FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0"
            )
            limite = time.monotonic() + 10
            while monitor.scalar(consulta) < 2:
                assert time.monotonic() < limite, "as duas vinculações não bloquearam na licença"
                time.sleep(0.02)  # polling da condição, não sincronização por tempo
        transacao.commit()
    finally:
        segurando.close()
        for thread in threads:
            thread.join(timeout=10)
    assert not any(thread.is_alive() for thread in threads)

    assert sorted(r.status_code for r in respostas) == [201, 409]
    recusada = next(r for r in respostas if r.status_code == 409)
    assert recusada.json()["regra"] == "BR-018"
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT count(*) FROM licenca_vinculo")) == 1
        recusas = conn.execute(
            text("SELECT regra_violada FROM audit_log WHERE resultado = 'RECUSADO'")
        ).all()
    assert recusas == [("BR-018",)]


def test_ux_licenca_ativo_conflito_real_grava_recusa_na_auditoria(client, db, cenario):
    """O índice parcial é a garantia de uma máquina por licença. Pela API o lock na licença
    serializa as vinculações; só um escritor externo que insira direto em licenca_vinculo (ETL,
    carga D.8) o provoca. Aqui ele é uma segunda conexão real que insere sem confirmar; a
    vinculação pela API bloqueia no índice e, quando a conexão externa confirma, recebe o
    IntegrityError real (NFR-AUD-05)."""
    maquina = cenario["maquinas"][0]
    externo = engine.connect()
    transacao_externa = externo.begin()
    pid_externo = externo.scalar(text("SELECT pg_backend_pid()"))
    externo.execute(text(VINCULO_SQL), {"l": cenario["licenca"], "a": maquina, "v": True})

    resultado = {}

    def vincular():
        resultado["resposta"] = client.post(
            f"/api/v1/licencas/{cenario['licenca']}/vinculos",
            headers=cenario["cabecalho"],
            json={"ativo_id": maquina},
        )

    thread = threading.Thread(target=vincular)
    thread.start()
    try:
        with _monitor() as monitor:
            consulta = text(
                "SELECT count(*) FROM pg_stat_activity WHERE :pid = ANY(pg_blocking_pids(pid))"
            )
            limite = time.monotonic() + 10
            while not monitor.scalar(consulta, {"pid": pid_externo}):
                assert time.monotonic() < limite, "a vinculação não bloqueou no índice"
                time.sleep(0.02)
        transacao_externa.commit()
    finally:
        externo.close()
        thread.join(timeout=10)
    assert not thread.is_alive()

    resposta = resultado["resposta"]
    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-034"
    with engine.connect() as conn:
        auditoria = conn.execute(
            text(
                "SELECT operacao, resultado, regra_violada FROM audit_log"
                " WHERE entidade = 'licenca_vinculo'"
            )
        ).all()
        vinculos = conn.scalar(text("SELECT count(*) FROM licenca_vinculo"))
    assert auditoria == [("CRIAR", "RECUSADO", "BR-034")]
    assert vinculos == 1  # só o do escritor externo


@pytest.mark.parametrize("ordem", [("vincular", "baixar"), ("baixar", "vincular")])
def test_br031_br032_baixa_e_vinculacao_disputam_a_maquina_sem_deixar_vinculo_ativo_em_baixada(
    client, db, cenario, ordem
):
    """Uma baixa e uma vinculação disputam a mesma máquina, nas duas ordens. Uma conexão externa
    segura o lock do ativo; as requisições bloqueiam nele, uma de cada vez, e entram na ordem em
    que bloquearam. Sem mock: conexões e transações reais."""
    from fastapi.testclient import TestClient

    from app.main import app

    app.dependency_overrides.clear()  # cada requisição usa a própria sessão e conexão
    licenca, maquina = cenario["licenca"], cenario["maquinas"][0]
    chamadas = {
        "vincular": lambda c: c.post(
            f"/api/v1/licencas/{licenca}/vinculos",
            headers=cenario["cabecalho"],
            json={"ativo_id": maquina},
        ),
        "baixar": lambda c: c.post(
            f"/api/v1/ativos/{maquina}/baixa",
            headers=cenario["cabecalho"],
            json={"motivo": "DEFEITO", "data_baixa": "2025-07-10", "destinacao": "DESCARTE"},
        ),
    }
    respostas = {}

    def executar(nome):
        with TestClient(app) as cliente:
            respostas[nome] = chamadas[nome](cliente)

    segurando = engine.connect()
    transacao = segurando.begin()
    segurando.execute(text("SELECT id FROM ativo WHERE id = :i FOR UPDATE"), {"i": maquina})
    threads = []
    try:
        with _monitor() as monitor:
            consulta = text(
                "SELECT count(*) FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0"
            )
            for posicao, nome in enumerate(ordem, start=1):
                thread = threading.Thread(target=executar, args=(nome,))
                threads.append(thread)
                thread.start()
                limite = time.monotonic() + 10
                while monitor.scalar(consulta) < posicao:  # polling da condição, não por tempo
                    assert time.monotonic() < limite, f"{nome} não bloqueou no lock do ativo"
                    time.sleep(0.02)
        transacao.commit()
    finally:
        segurando.close()
        for thread in threads:
            thread.join(timeout=10)
    assert not any(thread.is_alive() for thread in threads)

    with engine.connect() as conn:
        em_baixada = conn.scalar(
            text(
                "SELECT count(*) FROM licenca_vinculo v JOIN ativo a ON a.id = v.ativo_id"
                " WHERE v.ativo_vinculo AND a.status = 'BAIXADO'"
            )
        )
        vinculos = conn.execute(text("SELECT ativo_vinculo FROM licenca_vinculo")).all()
        encerramentos = conn.execute(
            text(
                "SELECT detalhe->>'origem' FROM audit_log"
                " WHERE entidade = 'licenca_vinculo' AND operacao = 'EXCLUIR'"
            )
        ).all()
        recusas = conn.execute(
            text("SELECT regra_violada FROM audit_log WHERE resultado = 'RECUSADO'")
        ).all()
    assert em_baixada == 0  # a invariante, em qualquer ordem
    assert respostas["baixar"].status_code == 201
    if ordem[0] == "vincular":
        # A baixa vê o vínculo recém-criado e o encerra: o assento volta.
        assert respostas["vincular"].status_code == 201
        assert vinculos == [(False,)]
        assert encerramentos == [("baixa",)]
        assert recusas == []
    else:
        assert respostas["vincular"].status_code == 409
        assert respostas["vincular"].json()["regra"] == "BR-032"
        assert vinculos == []
        assert encerramentos == []
        assert recusas == [("BR-032",)]


@pytest.mark.parametrize("ordem", [("vincular", "baixar"), ("baixar", "vincular")])
def test_br036_br037_baixa_do_software_e_vinculacao_disputam_a_licenca_sem_vinculo_ativo_em_baixado(
    client, db, cenario, categoria, fornecedor, ordem
):
    """Baixa do ativo SOFTWARE e vinculação à licença perpétua dele ao mesmo tempo, nas duas
    ordens. Uma conexão externa segura o lock do software; as requisições bloqueiam nele, uma de
    cada vez, e entram na ordem em que bloquearam. Sem mock: conexões e transações reais."""
    from fastapi.testclient import TestClient

    from app.main import app

    cabecalho = cenario["cabecalho"]
    software = client.post(
        "/api/v1/ativos",
        headers=cabecalho,
        json={
            "nome": "Software Conc",
            "tipo": "SOFTWARE",
            "categoria_id": categoria.id,
            "fornecedor_id": fornecedor.id,
            "chave_licenca": "K-SW-CONC",
            "data_aquisicao": "2025-01-10",
            "valor_compra": "500.00",
        },
    ).json()["id"]
    perpetua = client.post(
        "/api/v1/licencas",
        headers=cabecalho,
        json={
            "tipo_licenciamento": "PERPETUA",
            "ativo_id": software,
            "fornecedor_id": fornecedor.id,
            "chave_licenca": "PERP-1234-5678",
            "quantidade_contratada": 2,
            "data_inicio_vigencia": "2025-01-01",
            "data_expiracao": "2099-12-31",
        },
    ).json()["id"]
    maquina = cenario["maquinas"][0]

    app.dependency_overrides.clear()  # cada requisição usa a própria sessão e conexão
    chamadas = {
        "vincular": lambda c: c.post(
            f"/api/v1/licencas/{perpetua}/vinculos", headers=cabecalho, json={"ativo_id": maquina}
        ),
        "baixar": lambda c: c.post(
            f"/api/v1/ativos/{software}/baixa",
            headers=cabecalho,
            json={"motivo": "FIM_VIDA_UTIL", "data_baixa": "2025-07-10", "destinacao": "DESCARTE"},
        ),
    }
    respostas = {}

    def executar(nome):
        with TestClient(app) as cliente:
            respostas[nome] = chamadas[nome](cliente)

    segurando = engine.connect()
    transacao = segurando.begin()
    segurando.execute(text("SELECT id FROM ativo WHERE id = :i FOR UPDATE"), {"i": software})
    threads = []
    try:
        with _monitor() as monitor:
            consulta = text(
                "SELECT count(*) FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0"
            )
            for posicao, nome in enumerate(ordem, start=1):
                thread = threading.Thread(target=executar, args=(nome,))
                threads.append(thread)
                thread.start()
                limite = time.monotonic() + 10
                while monitor.scalar(consulta) < posicao:  # polling da condição, não por tempo
                    assert time.monotonic() < limite, f"{nome} não bloqueou no lock do software"
                    time.sleep(0.02)
        transacao.commit()
    finally:
        segurando.close()
        for thread in threads:
            thread.join(timeout=10)
    assert not any(thread.is_alive() for thread in threads)

    with engine.connect() as conn:
        em_baixado = conn.scalar(
            text(
                "SELECT count(*) FROM licenca_vinculo v JOIN licenca l ON l.id = v.licenca_id"
                " JOIN ativo a ON a.id = l.ativo_id WHERE v.ativo_vinculo AND a.status = 'BAIXADO'"
            )
        )
        vinculos = conn.execute(text("SELECT ativo_vinculo FROM licenca_vinculo")).all()
        encerramentos = conn.execute(
            text(
                "SELECT detalhe->>'origem' FROM audit_log"
                " WHERE entidade = 'licenca_vinculo' AND operacao = 'EXCLUIR'"
            )
        ).all()
        recusas = conn.execute(
            text("SELECT regra_violada FROM audit_log WHERE resultado = 'RECUSADO'")
        ).all()
    assert em_baixado == 0  # a invariante, em qualquer ordem
    assert respostas["baixar"].status_code == 201
    if ordem[0] == "vincular":
        # A baixa espera a vinculação terminar, vê o vínculo novo e o encerra.
        assert respostas["vincular"].status_code == 201
        assert vinculos == [(False,)]
        assert encerramentos == [("baixa",)]
        assert recusas == []
    else:
        assert respostas["vincular"].status_code == 409
        assert respostas["vincular"].json()["regra"] == "BR-037"
        assert vinculos == []
        assert encerramentos == []
        assert recusas == [("BR-037",)]
