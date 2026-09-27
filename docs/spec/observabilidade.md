# SPEC — Observabilidade

Parte de [SPEC — ITAM](README.md).

## 11. Observabilidade

### 11.1 Métricas expostas

| Métrica | Tipo | Labels |
|---|---|---|
| `itam_http_requests_total` | Counter | `method`, `endpoint`, `status` |
| `itam_http_request_duration_seconds` | Histogram | `method`, `endpoint` |
| `itam_ativos_total` | Gauge | `status` |
| `itam_licencas_nao_conformes` | Gauge | `motivo` |
| `itam_importacoes_total` | Counter | `resultado` |
| `itam_regras_violadas_total` | Counter | `regra` |

`itam_regras_violadas_total` é a métrica mais interessante do conjunto: permite demonstrar em Grafana, durante a defesa, quantas tentativas de operar em desconformidade o sistema bloqueou.

### 11.2 Log estruturado

JSON em uma linha por evento, com `timestamp`, `level`, `logger`, `mensagem`, `request_id`, `usuario_id` e `regra`. Nível configurável por `LOG_LEVEL`.

### 11.3 Grafana

Provisionamento automático: datasource Prometheus, pasta **Governança de TI**, dashboard com disponibilidade, requisições por minuto, distribuição de códigos de retorno, latência p50/p95/p99 e estado do banco.

