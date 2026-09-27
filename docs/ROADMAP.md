# Roadmap — ITAM

Snapshot de progresso contra os gates e sprints definidos em [`BACKLOG_E_GATES.md`](BACKLOG_E_GATES.md). Atualizar a cada gate liberado.

_Última atualização: 2026-09-27_

> Legenda: `[x]` concluído · `[ ]` pendente ou aguardando verificação. Observações após o travessão indicam o que ainda falta.

---

## Status por gate

| Gate | Tema | Status |
|---|---|---|
| Gate 0 | Enquadramento | Quase completo — falta CI |
| Gate 1 | Inventário operacional | Em andamento |
| Gate 2 | Responsabilidade e valor | Em andamento |
| Gate 3 | Conformidade e evento surpresa | Em andamento |
| Gate 4 | Decisão e defesa | Não iniciado |

---

## Sprint 0 — Preparação

- [x] Estrutura de pastas do SPEC
- [x] `docker-compose.yml` (API, PostgreSQL, Prometheus, Grafana)
- [x] Alembic inicializado (`alembic/env.py`) — sem migração base ainda (`alembic/versions/` vazio)
- [ ] CI (ruff, mypy, bandit, pytest) — sem workflow em `.github/`
- [ ] `openapi.yaml`
- [ ] ADR-001 a ADR-003 — ver `docs/adr/`
- [x] README e política de uso de IA

## Sprint 1 — Ingestão e inventário

- [x] Modelos `categoria`, `fornecedor`, `setor`, `responsavel`, `usuario`
- [x] Modelo `ativo`
- [ ] Autenticação JWT / hash — `app/core/security.py` existe; validar cobertura de AC-056
- [ ] Dependência `require_perfil` / RBAC — verificar `app/api/deps.py`
- [ ] Endpoints `POST/GET/PATCH /ativos` — `app/api/v1/router.py` ainda vazio, `routers/` sem arquivos
- [ ] Unicidade de número de série — verificar no modelo/migração
- [x] Pipeline de importação CSV/XLSX (`importacao_service.py`) — endpoint pendente
- [x] `LoteImportacao` / `ErroImportacao` (`app/models/importacao.py`)
- [x] Trilha de auditoria (`app/core/audit.py`, `app/models/auditoria.py`)
- [x] Handler global de erros (`app/core/exceptions.py`)

## Sprint 2 — Responsabilidade e depreciação

- [x] Modelo `historico_transferencia` (`app/models/historico.py`)
- [x] Serviço de responsável / transferência (`app/services/responsavel_service.py`) — endpoint pendente
- [x] `utils/depreciacao.py`
- [x] Serviço de depreciação (`app/services/depreciacao_service.py`)
- [ ] Endpoints `/ativos/{id}/depreciacao` e `/historico`

## Sprint 3 — Licenças, baixas e compliance

- [x] Modelos `licenca`, `baixa_ativo`
- [x] Serviços de licença, baixa e compliance (`licenca_service.py`, `baixa_service.py`, `compliance_service.py`)
- [ ] Endpoints correspondentes
- [ ] Regras CP-01 a CP-09 — verificar cobertura em `compliance_service.py`

## Sprint 4 — Indicadores, relatórios e observabilidade

- [x] Serviços de indicador e relatório (`indicador_service.py`, `relatorio_service.py`)
- [x] Exportação CSV/XLSX (`app/utils/exportacao.py`)
- [ ] Endpoints `/relatorios`, `/indicadores`, `/compliance/alertas`
- [ ] `/health`, `/metrics` — `app/core/metrics.py` existe; expor rotas pendente
- [ ] Provisionamento Grafana — ver `infra/`
- [x] Log estruturado JSON (`app/core/logging.py`)

## Sprint 5 — Decisão, qualidade e defesa

- [x] Serviços de cenário, scorecard, risco e recomendação (`cenario_service.py`, `scorecard_service.py`, `risco_service.py`, `recomendacao_service.py`)
- [ ] Endpoints correspondentes
- [ ] Testes de contrato — `tests/contract/` vazio
- [ ] Cobertura ≥ 70% / 100% em `utils` e `services` — `tests/unit/`, `tests/integration/` vazios, nenhum `test_*.py` no repositório
- [x] `scripts/smoke_test.sh` — arquivo existe; validar execução
- [ ] Roteiro de defesa

---

## Próximos passos (ordem sugerida)

- [ ] 1. Criar migração Alembic base (`alembic revision --autogenerate`) a partir dos modelos existentes.
- [ ] 2. Implementar routers em `app/api/v1/routers/` e registrar em `router.py` — a camada de serviço já está pronta, falta expor via API.
- [ ] 3. Escrever testes `test_ac###_...` para os critérios de aceite já implementáveis (modelos + serviços de Sprints 1–3).
- [ ] 4. Adicionar workflow de CI (`ruff`, `mypy`, `bandit`, `pytest`).
- [ ] 5. Gerar `openapi.yaml` a partir dos endpoints implementados.
- [ ] 6. Expor `/health` e `/metrics`, provisionar dashboard Grafana.

## Riscos do roadmap

- Camada de serviço adiantada em relação à camada de API e testes — risco de integração tardia sem testes de contrato.
- Ausência de CI significa que regressões não são pegas automaticamente até a escrita dos testes.
- Sem migração Alembic, banco não pode ser criado via `alembic upgrade head` como o SPEC exige (NFR-MAN-06).