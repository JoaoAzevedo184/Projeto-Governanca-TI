"""Observabilidade (FR-014): AC-053 (`/health`), AC-054 (`/metrics`), contador de regras
violadas, log sem dado sensível. Os contadores são globais ao processo, então os testes
comparam a diferença antes e depois da operação."""

import json
import logging

import pytest
from prometheus_client import REGISTRY
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.core.logging import JsonFormatter
from app.main import app


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _valor(nome, **rotulos):
    return REGISTRY.get_sample_value(nome, rotulos) or 0.0


def _violadas(regra):
    return _valor("itam_regras_violadas_total", regra=regra)


def _baixa(client, token, ativo_id):
    return client.post(
        f"/api/v1/ativos/{ativo_id}/baixa",
        headers=_headers(token),
        json={"motivo": "DEFEITO", "data_baixa": "2025-07-10", "destinacao": "DESCARTE"},
    )


def test_ac053_health_informa_aplicacao_ambiente_e_banco(client):
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "status": "UP",
        "environment": "local",
        "database": {"status": "UP", "dialect": "postgresql"},
        "version": "1.0.0",
    }


def test_ac053_health_com_o_banco_fora_do_ar_responde_503_e_database_down(client):
    motor = create_engine("postgresql+psycopg://itam:itam@127.0.0.1:1/itam?connect_timeout=1")
    sessao = sessionmaker(bind=motor)()

    def _banco_morto():
        yield sessao

    app.dependency_overrides[get_db] = _banco_morto
    try:
        resposta = client.get("/health")
        metricas = client.get("/metrics")
    finally:
        sessao.close()
        motor.dispose()

    assert resposta.status_code == 503
    assert resposta.json()["status"] == "DOWN"
    assert resposta.json()["database"]["status"] == "DOWN"
    assert metricas.status_code == 200  # o scrape não cai junto com o banco
    assert _valor("itam_database_up") == 0.0


def test_ac054_metrics_no_formato_de_exposicao_prometheus_e_publico(client):
    client.get("/health")

    resposta = client.get("/metrics")  # sem token

    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/plain; version=0.0.4")
    corpo = resposta.text
    for nome in (
        "itam_http_requests_total",
        "itam_http_request_duration_seconds_bucket",
        "itam_ativos_total",
        "itam_licencas_nao_conformes",
        "itam_importacoes_total",
        "itam_database_up",
    ):
        assert nome in corpo, nome
    assert "# TYPE itam_http_requests_total counter" in corpo
    assert "# TYPE itam_http_request_duration_seconds histogram" in corpo


def test_contador_de_requisicoes_usa_o_template_da_rota_e_o_status(client, token_admin, novo_ativo):
    ativo = novo_ativo()
    rotulos = {"method": "GET", "endpoint": "/api/v1/ativos/{ativo_id}"}
    antes_200 = _valor("itam_http_requests_total", status="200", **rotulos)
    antes_404 = _valor("itam_http_requests_total", status="404", **rotulos)
    antes_duracao = _valor("itam_http_request_duration_seconds_count", **rotulos)

    client.get(f"/api/v1/ativos/{ativo}", headers=_headers(token_admin))
    client.get("/api/v1/ativos/999999", headers=_headers(token_admin))

    assert _valor("itam_http_requests_total", status="200", **rotulos) == antes_200 + 1
    assert _valor("itam_http_requests_total", status="404", **rotulos) == antes_404 + 1
    assert _valor("itam_http_request_duration_seconds_count", **rotulos) == antes_duracao + 2
    assert f"/api/v1/ativos/{ativo}" not in client.get("/metrics").text  # sem série por id


def test_metrics_nao_conta_a_si_mesmo_e_rota_inexistente_tem_rotulo_fixo(client):
    antes = _valor("itam_http_requests_total", method="GET", endpoint="/metrics", status="200")
    desconhecida = _valor(
        "itam_http_requests_total", method="GET", endpoint="nao_encontrado", status="404"
    )

    client.get("/metrics")
    client.get("/rota/que/nao/existe")

    assert (
        _valor("itam_http_requests_total", method="GET", endpoint="/metrics", status="200") == antes
    )
    assert (
        _valor("itam_http_requests_total", method="GET", endpoint="nao_encontrado", status="404")
        == desconhecida + 1
    )


def test_recusa_por_regra_incrementa_o_contador_e_sucesso_nao(client, token_admin, novo_ativo):
    ativo = novo_ativo()
    antes = _violadas("BR-024")

    assert _baixa(client, token_admin, ativo).status_code == 201
    assert _violadas("BR-024") == antes  # a baixa válida não conta
    assert _violadas("None") == 0  # nem gera série sem regra: sucesso não passa pelo contador

    assert _baixa(client, token_admin, ativo).status_code == 409  # BR-024
    assert _violadas("BR-024") == antes + 1
    assert 'itam_regras_violadas_total{regra="BR-024"}' in client.get("/metrics").text


@pytest.mark.parametrize("fluxo", ["recusar_operacao", "responsavel", "cadastro_duplicado"])
def test_todo_caminho_de_recusa_auditada_passa_pelo_mesmo_ponto_do_contador(
    client, token_admin, novo_ativo, responsavel, setor, fluxo
):
    ativo = novo_ativo()
    if fluxo == "recusar_operacao":
        regra = "BR-024"  # core/audit.recusar_operacao
        _baixa(client, token_admin, ativo)
        acao = lambda: _baixa(client, token_admin, ativo)  # noqa: E731
    elif fluxo == "responsavel":
        regra = "BR-009"  # responsavel_service._recusar
        _baixa(client, token_admin, ativo)
        acao = lambda: client.post(  # noqa: E731
            f"/api/v1/ativos/{ativo}/responsavel",
            headers=_headers(token_admin),
            json={
                "responsavel_id": responsavel.id,
                "setor_id": setor.id,
                "data_inicio": "2025-02-01",
            },
        )
    else:
        regra = "BR-001"  # ativo_service, número de série duplicado
        acao = lambda: client.post(  # noqa: E731
            "/api/v1/ativos",
            headers=_headers(token_admin),
            json={
                "nome": "Duplicado",
                "tipo": "HARDWARE",
                "categoria_id": 1,
                "fornecedor_id": 1,
                "numero_serie": "SN-T1",
                "data_aquisicao": "2025-01-10",
                "valor_compra": "10.00",
            },
        )
    antes = _violadas(regra)

    resposta = acao()

    assert resposta.status_code == 409, resposta.text
    assert resposta.json()["regra"] == regra
    assert _violadas(regra) == antes + 1


def test_erro_de_validacao_e_permissao_negada_nao_contam_como_regra_violada(
    client, token_gestor, token_admin
):
    antes = _violadas("FR-015")

    negado = client.post(
        "/api/v1/setores", headers=_headers(token_gestor), json={"nome": "Setor X"}
    )
    invalido = client.post("/api/v1/setores", headers=_headers(token_admin), json={})

    assert (negado.status_code, invalido.status_code) == (403, 422)
    assert _violadas("FR-015") == antes


def test_gauges_de_negocio_refletem_o_estado_do_banco(
    client, token_admin, novo_ativo, nova_licenca
):
    ativo = novo_ativo()
    novo_ativo()
    _baixa(client, token_admin, ativo)
    nova_licenca(inicio="2019-01-01", expiracao="2020-01-01")  # vencida: CP-01

    client.get("/metrics")

    assert _valor("itam_ativos_total", status="ATIVO") == 1
    assert _valor("itam_ativos_total", status="BAIXADO") == 1
    assert _valor("itam_ativos_total", status="EM_MANUTENCAO") == 0
    assert _valor("itam_licencas_nao_conformes", motivo="vencida") == 1
    assert _valor("itam_licencas_nao_conformes", motivo="acima_do_contratado") == 0
    assert _valor("itam_database_up") == 1


def test_contador_de_importacoes_por_resultado(client, token_admin, categoria, fornecedor):
    def enviar(conteudo):
        return client.post(
            "/api/v1/importacoes",
            headers=_headers(token_admin),
            files={"arquivo": ("inv.csv", conteudo, "text/csv")},
        )

    cabecalho = "nome,tipo,categoria,fornecedor,numero_serie,data_aquisicao,valor_compra\n"
    base = f"HARDWARE,{categoria.nome},{fornecedor.razao_social}"
    ok = f"Notebook A,{base},SN-IMP-1,2025-01-10,10.00\n"
    ruim = f"Notebook B,{base},,2025-01-10,10.00\n"
    antes = {
        r: _valor("itam_importacoes_total", resultado=r)
        for r in ("sucesso", "parcial", "rejeitada", "arquivo_invalido")
    }

    assert enviar((cabecalho + ok).encode()).status_code == 202
    assert (
        enviar((cabecalho + ok.replace("SN-IMP-1", "SN-IMP-2") + ruim).encode()).status_code == 202
    )
    assert enviar((cabecalho + ruim).encode()).status_code == 202
    assert enviar(b"").status_code == 422

    for resultado in antes:
        assert _valor("itam_importacoes_total", resultado=resultado) == antes[resultado] + 1


def test_request_id_e_devolvido_e_aceita_o_de_entrada_se_for_simples(client):
    gerado = client.get("/health").headers["X-Request-ID"]
    aceito = client.get("/health", headers={"X-Request-ID": "trace-42_a.b"}).headers["X-Request-ID"]
    invalido = client.get("/health", headers={"X-Request-ID": "invalido com espaco!"}).headers[
        "X-Request-ID"
    ]

    assert len(gerado) == 32 and gerado.isalnum()
    assert aceito == "trace-42_a.b"
    assert invalido != "inválido com espaço!" and len(invalido) == 32


def _eventos(caplog):
    return [json.loads(JsonFormatter().format(r)) for r in caplog.records]


def test_log_de_acesso_traz_requisicao_usuario_e_request_id(client, token_admin, caplog):
    with caplog.at_level(logging.INFO):
        resposta = client.get("/api/v1/auth/me", headers=_headers(token_admin))

    acessos = [e for e in _eventos(caplog) if e["logger"] == "itam.http"]
    assert len(acessos) == 1
    acesso = acessos[0]
    assert (acesso["metodo"], acesso["caminho"], acesso["status"]) == (
        "GET",
        "/api/v1/auth/me",
        200,
    )
    assert acesso["usuario_id"] == resposta.json()["id"]
    assert acesso["request_id"] == resposta.headers["X-Request-ID"]
    assert acesso["duracao_ms"] >= 0


def test_scrape_do_metrics_nao_vai_para_o_log_de_acesso(client, caplog):
    with caplog.at_level(logging.INFO):
        client.get("/metrics")

    assert [e for e in _eventos(caplog) if e["logger"] == "itam.http"] == []


def test_log_da_recusa_traz_a_regra_e_o_request_id(client, token_admin, novo_ativo, caplog):
    ativo = novo_ativo()
    _baixa(client, token_admin, ativo)

    with caplog.at_level(logging.INFO):
        resposta = _baixa(client, token_admin, ativo)

    recusas = [e for e in _eventos(caplog) if e["logger"] == "itam" and e["regra"]]
    assert [(e["regra"], e["status"]) for e in recusas] == [("BR-024", 409)]
    assert recusas[0]["usuario_id"] is not None
    assert recusas[0]["request_id"] == resposta.headers["X-Request-ID"]


def test_log_nao_contem_senha_token_nem_chave_sem_mascara(client, token_admin, fornecedor, caplog):
    chave = "SEGREDO-ABCD-1234-EFGH"
    criada = client.post(
        "/api/v1/licencas",
        headers=_headers(token_admin),
        json={
            "tipo_licenciamento": "OEM",
            "software": "Windows OEM",
            "fornecedor_id": fornecedor.id,
            "chave_licenca": chave,
            "quantidade_contratada": 1,
            "data_inicio_vigencia": "2025-01-01",
            "data_expiracao": "2099-12-31",
        },
    )
    licenca = criada.json()["id"]

    with caplog.at_level(logging.DEBUG):
        client.post("/api/v1/auth/login", json={"login": "admin_teste", "senha": "senha-errada-99"})
        client.get(f"/api/v1/licencas/{licenca}", headers=_headers(token_admin))
        client.get("/api/v1/licencas", headers=_headers(token_admin))

    saida = "\n".join(JsonFormatter().format(r) for r in caplog.records)
    assert saida  # houve log para inspecionar
    assert "senha-errada-99" not in saida
    assert token_admin not in saida
    assert chave not in saida
    assert "SEGREDO-ABCD" not in saida
