"""Métricas Prometheus (NFR-OBS-01, NFR-OBS-02) e o middleware HTTP que as alimenta.

As métricas são as de docs/spec/observabilidade.md §11.1, mais `itam_database_up` (estado do
banco, que o dashboard do §11.3 pede). O rótulo `endpoint` é o caminho do *template* da rota
(`/api/v1/ativos/{ativo_id}`), nunca o caminho real, para não multiplicar séries por id.
"""

import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from prometheus_client import Counter, Gauge, Histogram

from app.core.logging import request_id_ctx

HTTP_REQUESTS = Counter(
    "itam_http_requests_total", "Requisições HTTP.", ["method", "endpoint", "status"]
)
HTTP_DURATION = Histogram(
    "itam_http_request_duration_seconds", "Duração das requisições HTTP.", ["method", "endpoint"]
)
ATIVOS_TOTAL = Gauge("itam_ativos_total", "Ativos por status.", ["status"])
LICENCAS_NAO_CONFORMES = Gauge(
    "itam_licencas_nao_conformes", "Licenças não conformes (CP-01, CP-02).", ["motivo"]
)
ATIVOS_POR_TIPO = Gauge("itam_ativos_por_tipo", "Ativos por tipo.", ["tipo"])
PATRIMONIO_REAIS = Gauge(
    "itam_patrimonio_reais",
    "Valor patrimonial dos ativos não baixados, em reais (`base`: compra ou residual).",
    ["base"],
)
LICENCAS_POR_CONFORMIDADE = Gauge(
    "itam_licencas_por_conformidade", "Licenças por status de conformidade.", ["status"]
)
COMPLIANCE_ALERTAS = Gauge(
    "itam_compliance_alertas", "Alertas de compliance abertos por severidade.", ["severidade"]
)
ATIVOS_SEM_RESPONSAVEL = Gauge(
    "itam_ativos_sem_responsavel", "Ativos em operação sem responsável (CP-04)."
)
METRICAS_NEGOCIO_UP = Gauge(
    "itam_metricas_negocio_up", "1 quando o último cálculo das métricas de negócio funcionou."
)
METRICAS_NEGOCIO_DURACAO = Gauge(
    "itam_metricas_negocio_duracao_segundos", "Duração do último cálculo das métricas de negócio."
)
IMPORTACOES_TOTAL = Counter("itam_importacoes_total", "Importações de inventário.", ["resultado"])
REGRAS_VIOLADAS = Counter(
    "itam_regras_violadas_total", "Operações recusadas por regra de negócio.", ["regra"]
)
DATABASE_UP = Gauge("itam_database_up", "1 quando o banco responde, 0 quando não.")

_ID_VALIDO = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_logger = logging.getLogger("itam.http")


def _endpoint(request: Request) -> str:
    rota = request.scope.get("route")
    return getattr(rota, "path", None) or "nao_encontrado"


def instrumentar(app: FastAPI) -> None:
    """Middleware HTTP: `request_id` (aceita o `X-Request-ID` de entrada se for simples), contador
    e histograma por rota, e um evento de log por requisição. `/metrics` fica fora das métricas
    e do log."""

    @app.middleware("http")
    async def _middleware(request: Request, call_next):
        recebido = request.headers.get("x-request-id", "")
        request_id = recebido if _ID_VALIDO.match(recebido) else uuid.uuid4().hex
        request_id_ctx.set(request_id)
        inicio = time.perf_counter()
        status = 500
        try:
            resposta = await call_next(request)
            status = resposta.status_code
            resposta.headers["X-Request-ID"] = request_id
            return resposta
        finally:
            duracao = time.perf_counter() - inicio
            endpoint = _endpoint(request)
            if endpoint != "/metrics":  # o scrape a cada 15 s não entra nas métricas nem no log
                HTTP_REQUESTS.labels(request.method, endpoint, str(status)).inc()
                HTTP_DURATION.labels(request.method, endpoint).observe(duracao)
                _logger.info(
                    "requisição concluída",
                    extra={
                        "metodo": request.method,
                        "caminho": request.url.path,
                        "status": status,
                        "duracao_ms": round(duracao * 1000, 2),
                        "usuario_id": getattr(request.state, "usuario_id", None),
                    },
                )
