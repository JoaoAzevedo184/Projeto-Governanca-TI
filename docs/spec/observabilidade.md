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
| `itam_ativos_por_tipo` | Gauge | `tipo` |
| `itam_patrimonio_reais` | Gauge | `base` |
| `itam_licencas_por_conformidade` | Gauge | `status` |
| `itam_compliance_alertas` | Gauge | `severidade` |
| `itam_ativos_sem_responsavel` | Gauge | — |
| `itam_metricas_negocio_up` | Gauge | — |
| `itam_metricas_negocio_duracao_segundos` | Gauge | — |

**Como cada métrica é alimentada** (Sprint 4):

- `itam_http_requests_total` e `itam_http_request_duration_seconds`: middleware HTTP em `core/metrics.py`. O rótulo `endpoint` é o *template* da rota (`/api/v1/ativos/{ativo_id}`), nunca o caminho real; rota inexistente vira `nao_encontrado`. `/metrics` não se mede a si mesmo.
- `itam_regras_violadas_total`: incrementado num único ponto, `registrar_auditoria` em `core/audit.py`, quando a linha gravada é `RECUSADO` com `regra_violada`. Toda recusa por regra de negócio (BR-xxx) é auditada por ali. Não contam: `422` de validação, `403` de permissão (`FR-015`) e o `409` genérico de unicidade sem BR (`flush_ou_conflito`), que não são recusa auditada por regra.
- `itam_ativos_total`, `itam_licencas_nao_conformes` e `itam_database_up`: recalculados do banco a cada leitura de `/metrics` (`observabilidade_service.atualizar_gauges`). `motivo` é `vencida` (CP-01) ou `acima_do_contratado` (CP-02). Com o banco fora do ar, o scrape continua respondendo e `itam_database_up` vai a 0. `itam_database_up` não estava na tabela original; o dashboard do §11.3 pede "estado do banco".
- **Métricas de negócio do Gate 4** (leitura, calculadas do banco a cada `/metrics`; nada é armazenado): `itam_ativos_total{status}` (já existia), `itam_ativos_por_tipo{tipo}` (`HARDWARE`, `SOFTWARE`), `itam_patrimonio_reais{base}` (`compra`: soma de `valor_compra`; `residual`: soma do valor residual, ambas dos ativos **não baixados**, em reais), `itam_licencas_por_conformidade{status}` (`CONFORME`, `ALERTA`, `NAO_CONFORME`, como o `status_conformidade` de FR-004), `itam_compliance_alertas{severidade}` (`CRITICO`, `ALTO`, `MEDIO`, `BAIXO`) e `itam_ativos_sem_responsavel` (alertas CP-04). Reaproveitam os services (`calcular_indicadores`, IND-01 a IND-04, e `apurar_alertas`); nenhuma fórmula é refeita em `observabilidade_service.py`. Todo rótulo é reescrito a cada leitura, inclusive com valor 0.
- **Falha isolada:** se o cálculo de negócio falhar (erro de SQL ou de código), `atualizar_gauges` desfaz a transação, registra o erro no log (`falha ao calcular as métricas de negócio`) e põe `itam_metricas_negocio_up = 0`; `/metrics` segue com status 200 e as métricas técnicas intactas. Os gauges de negócio ficam com o último valor lido até o cálculo voltar (o dashboard mostra o aviso). `itam_metricas_negocio_duracao_segundos` é a duração do último cálculo.
- **Custo medido** (banco da demonstração, 96 ativos, 3 licenças): cálculo de negócio de 20 a 25 ms; `/metrics` inteiro com mediana de 16 ms e pior caso de 30 ms em 30 leituras locais (`/health`, 4 ms). Abaixo de 200 ms, então o cálculo roda a cada leitura, sem intervalo de atualização. Com o Prometheus lendo a cada 15 s, são cerca de 25 ms de banco por 15 s. **Limite conhecido:** `calcular_indicadores` carrega os ativos e agrega em Python (`ponytail` no `indicador_service.py`); se o parque passar de dezenas de milhares de ativos e a duração passar de 200 ms, guardar o resultado por um intervalo (por exemplo 60 s) em vez de recalcular a cada leitura.
- `itam_importacoes_total`: `resultado` é `sucesso` (nenhuma linha rejeitada), `parcial`, `rejeitada` (nenhuma aceita) ou `arquivo_invalido` (arquivo recusado antes de criar o lote).

`itam_regras_violadas_total` é a métrica mais interessante do conjunto: permite demonstrar em Grafana, durante a defesa, quantas tentativas de operar em desconformidade o sistema bloqueou.

### 11.2 Log estruturado

JSON em uma linha por evento, com `timestamp`, `level`, `logger`, `mensagem`, `request_id`, `usuario_id` e `regra`. Nível configurável por `LOG_LEVEL`. Eventos de requisição trazem também `metodo`, `caminho`, `status` e `duracao_ms`; a recusa por regra gera um evento com `regra`. O `request_id` vem do cabeçalho `X-Request-ID` quando ele é simples (`[A-Za-z0-9._-]`, até 64), senão é gerado, e volta no mesmo cabeçalho da resposta. `usuario_id` sai preenchido nas rotas autenticadas.

**Nada sensível no log** (`core/logging.py`): o formatador mascara chave de licença (`****-****-A3F9`), bearer e JWT, valores de `senha`, `password`, `token`, `secret` e semelhantes, e os `[parameters: ...]` de SQL que o SQLAlchemy anexa às mensagens de erro. Query string não é logada, e o scrape de `/metrics` fica fora do log.

### 11.3 Grafana

Provisionamento automático: datasource Prometheus, pasta **Governança de TI**, dashboard com disponibilidade, requisições por minuto, distribuição de códigos de retorno, latência p50/p95/p99 e estado do banco. Implementado em `infra/grafana/dashboards/itam.json` (uid `itam-tecnico`, pasta **Governança de TI**), mais os painéis de licenças não conformes, ativos por status e operações bloqueadas por regra. O datasource tem `uid: prometheus`, referenciado pelo dashboard.

**Dashboard gerencial (FR-014).** `infra/grafana/dashboards/itam-gestao.json`, título **ITAM - Gestão**, uid `itam-gestao`, na mesma pasta **Governança de TI** (o mesmo provedor lê os dois arquivos; o `itam-tecnico` não foi alterado). Painéis: total de ativos, ativos sem responsável, valor patrimonial de compra, valor residual, licenças não conformes, estado do cálculo de negócio, ativos por status, hardware x software, licenças por status de conformidade, alertas por severidade e dois gráficos no tempo (patrimônio e alertas). Atualiza a cada 30 s. O teste `test_dashboard_de_gestao_usa_so_metricas_que_o_metrics_expoe` garante que toda métrica usada existe em `/metrics`.

