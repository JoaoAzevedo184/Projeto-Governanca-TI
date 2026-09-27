# Roadmap — ITAM

Snapshot de progresso contra os gates e sprints definidos em [`BACKLOG_E_GATES.md`](BACKLOG_E_GATES.md). Atualizar a cada gate liberado.

_Última atualização: 2026-09-27_

> Legenda: `[x]` concluído · `[ ]` pendente ou aguardando verificação. Observações após o travessão indicam o que ainda falta.

---

## Status por gate

| Gate | Tema | Status |
|---|---|---|
| Gate 0 | Enquadramento | Completo |
| Gate 1 | Inventário operacional | Em andamento |
| Gate 2 | Responsabilidade e valor | Em andamento |
| Gate 3 | Conformidade e evento surpresa | Em andamento |
| Gate 4 | Decisão e defesa | Não iniciado |

---

## Sprint 0 — Preparação

- [x] Estrutura de pastas do SPEC
- [x] `docker-compose.yml` (API, PostgreSQL, Prometheus, Grafana)
- [x] Alembic funcional — `env.py` lê `DATABASE_URL` de `app/core/config.py`, `target_metadata = Base.metadata`; migração base `8b17f25f113a_base` aplicada e revertida (upgrade/downgrade testados)
- [x] CI (ruff, mypy, bandit, pytest) — `.github/workflows/ci.yml` (estava em `.github/.workflow/`, caminho inválido para o GitHub Actions; corrigido)
- [x] `openapi.yaml` — esqueleto inicial (`python/api/openapi.yaml`), `paths` preenchidos por sprint
- [x] ADR-001 a ADR-003 — resumidas em `docs/spec/adrs-e-rastreabilidade.md`
- [x] README e política de uso de IA
- [ ] Papéis da equipe — `docs/guia/equipe-e-ia.md` com nomes por preencher (não automatizável)

## Sprint 1 — Ingestão e inventário

- [x] `Base` e mixin de timestamp (`app/models/base.py`) — pré-requisito para os modelos abaixo, feito junto com o Sprint 0 (Alembic precisava de `target_metadata`)
- [ ] Modelos `categoria`, `fornecedor`, `setor`, `responsavel`, `usuario` — arquivos existem em `app/models/` mas estão vazios (scaffold)
- [ ] Modelo `ativo` — idem, `app/models/ativo.py` vazio
- [ ] Autenticação JWT / hash — `app/core/security.py` vazio
- [ ] Dependência `require_perfil` / RBAC — `app/api/deps.py` vazio
- [ ] Endpoints `POST/GET/PATCH /ativos` — `app/api/v1/router.py` e `routers/` vazios
- [ ] Unicidade de número de série
- [ ] Pipeline de importação CSV/XLSX — `importacao_service.py` vazio
- [ ] `LoteImportacao` / `ErroImportacao` — `app/models/importacao.py` vazio
- [ ] Trilha de auditoria — `app/core/audit.py`, `app/models/auditoria.py` vazios
- [ ] Handler global de erros — `app/core/exceptions.py` vazio

## Sprint 2 — Responsabilidade e depreciação

- [ ] Modelo `historico_transferencia` — `app/models/historico.py` vazio
- [ ] Serviço de responsável / transferência — `app/services/responsavel_service.py` vazio
- [ ] `utils/depreciacao.py` — vazio
- [ ] Serviço de depreciação — `app/services/depreciacao_service.py` vazio
- [ ] Endpoints `/ativos/{id}/depreciacao` e `/historico`

## Sprint 3 — Licenças, baixas e compliance

- [ ] Modelos `licenca`, `baixa_ativo` — vazios
- [ ] Serviços de licença, baixa e compliance — `licenca_service.py`, `baixa_service.py`, `compliance_service.py` vazios
- [ ] Endpoints correspondentes
- [ ] Regras CP-01 a CP-09

## Sprint 4 — Indicadores, relatórios e observabilidade

- [ ] Serviços de indicador e relatório — `indicador_service.py`, `relatorio_service.py` vazios
- [ ] Exportação CSV/XLSX — `app/utils/exportacao.py` vazio
- [ ] Endpoints `/relatorios`, `/indicadores`, `/compliance/alertas`
- [ ] `/health`, `/metrics` — `app/core/metrics.py` vazio
- [ ] Provisionamento Grafana — datasource pronto em `infra/`, falta o dashboard e a rota `/metrics` para ele ler
- [ ] Log estruturado JSON — `app/core/logging.py` vazio

## Sprint 5 — Decisão, qualidade e defesa

- [ ] Serviços de cenário, scorecard, risco e recomendação — `cenario_service.py`, `scorecard_service.py`, `risco_service.py`, `recomendacao_service.py` vazios
- [ ] Endpoints correspondentes
- [ ] Testes de contrato — `tests/contract/` vazio
- [ ] Cobertura ≥ 70% / 100% em `utils` e `services` — nenhum `test_*.py` no repositório
- [x] `scripts/smoke_test.sh` — arquivo existe; validar execução quando `/health` estiver exposto
- [ ] Roteiro de defesa

---

## Próximos passos (ordem sugerida)

- [ ] 1. Implementar os modelos SQLAlchemy de Sprint 1 (`categoria`, `fornecedor`, `setor`, `responsavel`, `usuario`, `ativo`) — os arquivos em `app/models/` existem mas ainda estão vazios (scaffold, não implementação).
- [ ] 2. Gerar a migração correspondente (`alembic revision --autogenerate`) a partir desses modelos.
- [ ] 3. Implementar os serviços e endpoints de Sprint 1 e registrar em `app/api/v1/router.py`.
- [ ] 4. Escrever testes `test_ac###_...` para os critérios de aceite implementados.
- [ ] 5. Gerar `openapi.yaml` a partir dos endpoints implementados.
- [ ] 6. Expor `/health` e `/metrics`, provisionar dashboard Grafana.

## Riscos do roadmap

- Os arquivos em `app/models/` e `app/services/` são placeholders vazios (0 bytes) — só a estrutura de pastas existe, não a implementação (ver Sprints 1–5 acima).
- Camada de serviço ainda não implementada — risco de integração tardia sem testes de contrato quando a implementação começar.