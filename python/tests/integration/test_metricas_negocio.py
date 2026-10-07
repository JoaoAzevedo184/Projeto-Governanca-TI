"""Métricas de negócio em `/metrics` (FR-014, Gate 4): gauges calculados do banco pelos services
existentes a cada leitura, sem derrubar `/metrics` nem as métricas técnicas quando o cálculo falha.

Os gauges são globais ao processo, mas cada leitura reescreve todos os rótulos, então o teste lê o
valor depois de uma leitura de `/metrics`. Valores esperados calculados à mão no próprio teste.
"""

import json
import re
from datetime import timedelta
from pathlib import Path

import pytest
from prometheus_client import REGISTRY
from sqlalchemy import text

from app.core.database import engine
from app.seed_demo import menos_meses
from app.services import observabilidade_service
from app.utils import datas


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _valor(nome, **rotulos):
    return REGISTRY.get_sample_value(nome, rotulos)


@pytest.fixture
def parque(client, token_admin, novo_ativo, nova_licenca, responsavel, setor):
    """Parque pequeno com resultado conhecido (a categoria tem vida útil de 60 meses):
    A  hardware R$ 6.000,00 comprado há 12 meses: residual 6.000 - 6.000 x 12 / 60 = 4.800,00
    B  hardware R$ 1.000,00 comprado hoje, com responsável: residual 1.000,00
    C  software R$ 500,00 comprado hoje: residual 500,00
    D  hardware R$ 3.000,00 baixado: fora do patrimônio
    Licenças: uma conforme, uma vencida (CP-01) e uma que vence em 10 dias (CP-03)."""
    hoje = datas.hoje()
    novo_ativo(valor="6000.00", data_aquisicao=menos_meses(hoje, 12).isoformat())
    b = novo_ativo(valor="1000.00", data_aquisicao=hoje.isoformat())
    novo_ativo(tipo="SOFTWARE", valor="500.00", data_aquisicao=hoje.isoformat())
    d = novo_ativo(valor="3000.00")
    assert (
        client.post(
            f"/api/v1/ativos/{b}/responsavel",
            headers=_headers(token_admin),
            json={
                "responsavel_id": responsavel.id,
                "setor_id": setor.id,
                "data_inicio": hoje.isoformat(),
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/api/v1/ativos/{d}/baixa",
            headers=_headers(token_admin),
            json={"motivo": "DEFEITO", "data_baixa": "2025-07-10", "destinacao": "DESCARTE"},
        ).status_code
        == 201
    )
    nova_licenca()
    nova_licenca(inicio="2019-01-01", expiracao="2020-01-01")
    nova_licenca(expiracao=(hoje + timedelta(days=10)).isoformat())


def test_metrics_expoe_os_indicadores_de_negocio_calculados_do_banco(client, parque):
    resposta = client.get("/metrics")

    assert resposta.status_code == 200
    # ativos por status e por tipo (D baixado conta; hardware: A, B, D; software: C)
    assert _valor("itam_ativos_total", status="ATIVO") == 3
    assert _valor("itam_ativos_total", status="BAIXADO") == 1
    assert _valor("itam_ativos_por_tipo", tipo="HARDWARE") == 3
    assert _valor("itam_ativos_por_tipo", tipo="SOFTWARE") == 1
    # patrimônio dos não baixados: compra 6.000 + 1.000 + 500; residual 4.800 + 1.000 + 500
    assert _valor("itam_patrimonio_reais", base="compra") == 7500.0
    assert _valor("itam_patrimonio_reais", base="residual") == 6300.0
    # licenças: uma de cada status
    assert _valor("itam_licencas_por_conformidade", status="CONFORME") == 1
    assert _valor("itam_licencas_por_conformidade", status="ALERTA") == 1
    assert _valor("itam_licencas_por_conformidade", status="NAO_CONFORME") == 1
    # alertas: CP-01 crítico; CP-03 e os 2 ativos ATIVO sem responsável (A e C) são altos
    assert _valor("itam_compliance_alertas", severidade="CRITICO") == 1
    assert _valor("itam_compliance_alertas", severidade="ALTO") == 3
    assert _valor("itam_compliance_alertas", severidade="MEDIO") == 0
    assert _valor("itam_ativos_sem_responsavel") == 2
    assert _valor("itam_metricas_negocio_up") == 1
    assert _valor("itam_metricas_negocio_duracao_segundos") > 0
    for nome in ("itam_patrimonio_reais", "itam_compliance_alertas", "itam_ativos_por_tipo"):
        assert f"# TYPE {nome} gauge" in resposta.text


def test_banco_vazio_zera_os_gauges_de_negocio_sem_erro(client):
    resposta = client.get("/metrics")

    assert resposta.status_code == 200
    assert _valor("itam_patrimonio_reais", base="compra") == 0
    assert _valor("itam_patrimonio_reais", base="residual") == 0
    assert _valor("itam_ativos_sem_responsavel") == 0
    assert _valor("itam_licencas_por_conformidade", status="CONFORME") == 0
    assert _valor("itam_metricas_negocio_up") == 1


def test_o_valor_muda_com_o_banco_a_cada_leitura(client, parque, token_admin):
    client.get("/metrics")
    assert _valor("itam_ativos_sem_responsavel") == 2

    ativo_a = 1
    client.post(
        f"/api/v1/ativos/{ativo_a}/baixa",
        headers=_headers(token_admin),
        json={
            "motivo": "DEFEITO",
            "data_baixa": datas.hoje().isoformat(),
            "destinacao": "DESCARTE",
        },
    )
    client.get("/metrics")

    assert _valor("itam_ativos_sem_responsavel") == 1  # só o C
    assert _valor("itam_patrimonio_reais", base="compra") == 1500.0  # 1.000 + 500


def test_falha_no_calculo_de_negocio_nao_derruba_o_metrics_nem_as_metricas_tecnicas(
    client, parque, monkeypatch, caplog
):
    client.get("/health")
    requisicoes = _valor("itam_http_requests_total", method="GET", endpoint="/health", status="200")

    def _quebra(*_args, **_kwargs):
        raise RuntimeError("falha simulada no cálculo")

    monkeypatch.setattr(observabilidade_service, "calcular_indicadores", _quebra)
    resposta = client.get("/metrics")

    assert resposta.status_code == 200
    assert _valor("itam_metricas_negocio_up") == 0
    assert _valor("itam_database_up") == 1  # o banco está bem
    assert "itam_http_request_duration_seconds_bucket" in resposta.text  # métricas técnicas
    assert (
        _valor("itam_http_requests_total", method="GET", endpoint="/health", status="200")
        == requisicoes
    )
    assert "falha ao calcular as métricas de negócio" in caplog.text
    monkeypatch.undo()
    client.get("/metrics")
    assert _valor("itam_metricas_negocio_up") == 1  # volta sozinho quando o cálculo volta


def test_falha_real_do_banco_no_calculo_nao_derruba_o_metrics(client, parque):
    """Erro de SQL de verdade: a coluna que os services leem some por instantes."""
    with engine.begin() as conexao:
        conexao.execute(text("SET LOCAL lock_timeout = '5s'"))
        conexao.execute(text("ALTER TABLE ativo RENAME COLUMN valor_compra TO valor_compra_x"))
    try:
        resposta = client.get("/metrics")
        up = _valor("itam_metricas_negocio_up")
        banco = _valor("itam_database_up")
    finally:
        with engine.begin() as conexao:
            conexao.execute(text("SET LOCAL lock_timeout = '5s'"))
            conexao.execute(text("ALTER TABLE ativo RENAME COLUMN valor_compra_x TO valor_compra"))

    assert resposta.status_code == 200
    assert (up, banco) == (0, 1)
    assert "itam_http_request_duration_seconds_bucket" in resposta.text
    client.get("/metrics")
    assert _valor("itam_metricas_negocio_up") == 1


DASHBOARDS = Path(__file__).resolve().parents[3] / "infra" / "grafana" / "dashboards"


def test_dashboard_de_gestao_usa_so_metricas_que_o_metrics_expoe(client, parque):
    dashboard = json.loads((DASHBOARDS / "itam-gestao.json").read_text(encoding="utf-8"))
    tecnico = json.loads((DASHBOARDS / "itam.json").read_text(encoding="utf-8"))
    exposto = client.get("/metrics").text
    usadas = {
        nome
        for painel in dashboard["panels"]
        for alvo in painel["targets"]
        for nome in re.findall(r"itam_[a-z_]+", alvo["expr"])
    }

    assert dashboard["title"] == "ITAM - Gestão" and dashboard["uid"] == "itam-gestao"
    assert dashboard["uid"] != tecnico["uid"]  # o técnico segue como está, com outro uid
    assert len({p["id"] for p in dashboard["panels"]}) == len(dashboard["panels"])
    assert {
        "itam_ativos_total",
        "itam_ativos_por_tipo",
        "itam_patrimonio_reais",
        "itam_licencas_por_conformidade",
        "itam_compliance_alertas",
        "itam_ativos_sem_responsavel",
    } <= usadas
    for nome in usadas:
        assert f"# TYPE {nome} " in exposto, nome
    assert {p["datasource"]["uid"] for p in dashboard["panels"]} == {"prometheus"}
