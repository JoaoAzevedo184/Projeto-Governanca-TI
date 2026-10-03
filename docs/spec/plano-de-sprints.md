# SPEC — Plano de Sprints

Parte de [SPEC — ITAM](README.md).

## 14. Plano de Sprints

| Sprint | Entregas técnicas | Critérios cobertos |
|---|---|---|
| **0** | Repositório, estrutura de pastas, Docker Compose, Alembic, CI, `openapi.yaml` inicial, ADRs 001–003 | — |
| **1** | Modelos e migrações de `categoria`, `fornecedor`, `setor`, `responsavel`, `ativo`, `usuario`; auth + RBAC; CRUD de ativos; importação CSV/XLSX | AC-001 a AC-008, AC-044 a AC-046, AC-055 a AC-057 |
| **2** | `historico_transferencia` com índice único parcial e triggers; endpoint de responsável; `utils/depreciacao.py`; endpoint de depreciação | AC-009 a AC-020 |
| **3** | `licenca`, `licenca_vinculo`, bloqueio de excedente; `baixa_ativo` com congelamento de valor residual | AC-021 a AC-033, AC-058 a AC-064 |
| **4** | Relatórios com filtros e exportação; painel de compliance; indicadores; `/health`, `/metrics`, Grafana provisionado | AC-034 a AC-043, AC-047, AC-053, AC-054; pendentes da Sprint 3: AC-022, AC-023, AC-031; BR-038 e AC-065, AC-066 |
| **5** | Cenários, scorecard, riscos, recomendação rastreável; testes de contrato; documentação final; smoke test; defesa | AC-048 a AC-052 |

**Definition of Done por sprint:** código na branch principal · migração aplicada e reversível · testes dos critérios da sprint passando · `openapi.yaml` regenerado e versionado · `docker compose up` sobe o ambiente sem intervenção manual · README atualizado se houve mudança de execução.

