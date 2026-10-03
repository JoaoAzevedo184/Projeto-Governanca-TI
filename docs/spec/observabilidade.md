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
| `itam_database_up` | Gauge | — |

**Como cada métrica é alimentada** (Sprint 4):

- `itam_http_requests_total` e `itam_http_request_duration_seconds`: middleware HTTP em `core/metrics.py`. O rótulo `endpoint` é o *template* da rota (`/api/v1/ativos/{ativo_id}`), nunca o caminho real; rota inexistente vira `nao_encontrado`. `/metrics` não se mede a si mesmo.
- `itam_regras_violadas_total`: incrementado num único ponto, `registrar_auditoria` em `core/audit.py`, quando a linha gravada é `RECUSADO` com `regra_violada`. Toda recusa por regra de negócio (BR-xxx) é auditada por ali. Não contam: `422` de validação, `403` de permissão (`FR-015`) e o `409` genérico de unicidade sem BR (`flush_ou_conflito`), que não são recusa auditada por regra.
- `itam_ativos_total`, `itam_licencas_nao_conformes` e `itam_database_up`: recalculados do banco a cada leitura de `/metrics` (`observabilidade_service.atualizar_gauges`). `motivo` é `vencida` (CP-01) ou `acima_do_contratado` (CP-02). Com o banco fora do ar, o scrape continua respondendo e `itam_database_up` vai a 0. `itam_database_up` não estava na tabela original; o dashboard do §11.3 pede "estado do banco".
- `itam_importacoes_total`: `resultado` é `sucesso` (nenhuma linha rejeitada), `parcial`, `rejeitada` (nenhuma aceita) ou `arquivo_invalido` (arquivo recusado antes de criar o lote).

`itam_regras_violadas_total` é a métrica mais interessante do conjunto: permite demonstrar em Grafana, durante a defesa, quantas tentativas de operar em desconformidade o sistema bloqueou.

### 11.2 Log estruturado

JSON em uma linha por evento, com `timestamp`, `level`, `logger`, `mensagem`, `request_id`, `usuario_id` e `regra`. Nível configurável por `LOG_LEVEL`. Eventos de requisição trazem também `metodo`, `caminho`, `status` e `duracao_ms`; a recusa por regra gera um evento com `regra`. O `request_id` vem do cabeçalho `X-Request-ID` quando ele é simples (`[A-Za-z0-9._-]`, até 64), senão é gerado, e volta no mesmo cabeçalho da resposta. `usuario_id` sai preenchido nas rotas autenticadas.

**Nada sensível no log** (`core/logging.py`): o formatador mascara chave de licença (`****-****-A3F9`), bearer e JWT, valores de `senha`, `password`, `token`, `secret` e semelhantes, e os `[parameters: ...]` de SQL que o SQLAlchemy anexa às mensagens de erro. Query string não é logada, e o scrape de `/metrics` fica fora do log.

### 11.3 Grafana

Provisionamento automático: datasource Prometheus, pasta **Governança de TI**, dashboard com disponibilidade, requisições por minuto, distribuição de códigos de retorno, latência p50/p95/p99 e estado do banco. Implementado em `infra/grafana/dashboards/itam.json` (uid `itam-tecnico`, pasta **Governança de TI**), mais os painéis de licenças não conformes, ativos por status e operações bloqueadas por regra. O datasource tem `uid: prometheus`, referenciado pelo dashboard.

