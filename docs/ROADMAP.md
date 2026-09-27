# Roadmap — ITAM

Snapshot de progresso contra os gates e sprints definidos em [`BACKLOG_E_GATES.md`](BACKLOG_E_GATES.md). Atualizar a cada gate liberado.

_Última atualização: 2026-09-27_

> Legenda: `[x]` concluído · `[ ]` pendente ou aguardando verificação. Observações após o travessão indicam o que ainda falta.

---

## Status por gate

| Gate | Tema | Status |
|---|---|---|
| Gate 0 | Enquadramento | Completo |
| Gate 1 | Inventário operacional | Aguardando liberação (importar arquivo real de 100 linhas) |
| Gate 2 | Responsabilidade e valor | Não iniciado |
| Gate 3 | Conformidade e evento surpresa | Não iniciado |
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

- [x] `Base` e mixin de timestamp (`app/models/base.py`)
- [x] Modelos `categoria`, `fornecedor`, `setor`, `responsavel`, `usuario`
- [x] Modelo `ativo` — `ck_ativo_identificador`, unicidade de `numero_serie`, índices (status, categoria_id, fornecedor_id, data_aquisicao)
- [x] Autenticação JWT (`app/core/security.py`) e hash BCrypt (passlib)
- [x] Dependência `require_perfil` / RBAC (`app/api/deps.py`)
- [x] Endpoints `POST/GET/PATCH /ativos` com paginação e filtros (status, tipo, categoria, fornecedor, busca)
- [x] Unicidade de número de série (BR-001, AC-002)
- [x] Validações de data e valor (BR-003, BR-004 — via `model_validator`/`Field`, 422)
- [x] Herança de vida útil da categoria (BR-006, AC-007)
- [x] Pipeline de importação CSV/XLSX (pandas) — cabeçalho, duplicidade no arquivo e na base, isolamento por linha
- [x] `LoteImportacao` / `ErroImportacao`
- [x] Trilha de auditoria em toda escrita (`app/core/audit.py`, AC-057)
- [x] Handler global de erros com campo `regra` (`app/core/exceptions.py`, padrão RFC 7807 do SPEC)
- [x] Migração `13ade34ba8a3` (tabelas de Sprint 1) — aplicada e revertida
- [x] Cadastros de apoio (`/categorias` com `GET/PATCH /{id}`, `/fornecedores`, `/setores`, `/responsaveis`) — CRUD, 404, 422, unicidade (409, via `flush_ou_conflito`) e auditoria testados em `tests/integration/test_cadastros.py`
- [x] Matriz RBAC completa das rotas existentes (`tests/integration/test_seguranca.py`) — parametrizada pelos 4 perfis (ADMIN, OPERADOR, GESTOR, AUDITOR) × todas as rotas de `docs/spec/contrato-api.md` §6.2/6.3/6.6, mais um teste dedicado de "sem token → 401" em todas elas, inclusive `GET /auth/me`
- [x] `POST/PATCH` de categoria/fornecedor/setor/responsável agora registram auditoria (`app/services/{categoria,fornecedor,setor,responsavel}_service.py`) — antes só `ativo`/`importação` registravam, violava AC-057/BR-030
- [x] 47 testes (`tests/integration/`) — 19 seguem a convenção `test_ac###_...`, 28 são testes de suporte (CRUD/RBAC/404/422 sem AC dedicado); 96% de cobertura em `app/`, `ruff`/`mypy`/`bandit` limpos
- **Observação:** a unicidade de `categoria.nome`, `fornecedor.cnpj`, `setor.nome` e `responsavel.matricula` (docs/spec/modelo-fisico.md) não tem BR associado no PRD — é `UNIQUE` de schema, sem regra de negócio numerada (diferente de `ativo.numero_serie`, que é BR-001). Equipe decide se formaliza um BR ou mantém como restrição de schema.
- **Decisão pausada:** `POST /importacoes` para ADMIN+OPERADOR foi proposto e barrado por contradizer `docs/prd/jornadas-historias.md` (US-031/US-032, "Como Administrador de TI"). Continua ADMIN-only; `GET /importacoes*` foi aberto aos 4 perfis (decisão sem contradição, registrada em `docs/REGISTRO_USO_DE_IA.md`)

## Sprint 2 — Responsabilidade e depreciação

- [ ] Modelo `historico_transferencia` — `app/models/historico.py` vazio
- [ ] Serviço de responsável / transferência — `app/services/responsavel_service.py` vazio
- [ ] `utils/depreciacao.py` — vazio
- [ ] Serviço de depreciação — `app/services/depreciacao_service.py` vazio
- [ ] Endpoints `/ativos/{id}/depreciacao` e `/historico`
- [ ] Bloco `depreciacao` na resposta de `POST/GET /ativos` (contrato da API) — depende de `utils/depreciacao.py` acima; adiado do Sprint 1

## Sprint 3 — Licenças, baixas e compliance

- [ ] Modelos `licenca`, `baixa_ativo` — vazios
- [ ] Serviços de licença, baixa e compliance — `licenca_service.py`, `baixa_service.py`, `compliance_service.py` vazios
- [ ] Endpoints correspondentes
- [ ] Regras CP-01 a CP-09
- [ ] Mascaramento de `chave_licenca` em listagens (RI-08, `****-****-A3F9`, completa só no detalhe e só para ADMIN) — adiado do Sprint 1, natural aqui por tratar do módulo de licenças

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
- [ ] Cobertura ≥ 70% global / 100% em `utils` e `services` — hoje: 96% global (passa), 93% no escopo `utils+services` (subiu de 90%: `categoria_service.py`/`fornecedor_service.py`/`responsavel_service.py`/`setor_service.py` 100%, `ativo_service.py` 96%, `importacao_service.py` 86%, `utils/*` ainda vazio); o job "Cobertura de 100% em utils/ e services/" do CI **continua falhando** (verificado: `exit 2`, "total of 93 is less than fail-under=100")
- [x] `scripts/smoke_test.sh` — arquivo existe; validar execução quando `/health` estiver exposto
- [ ] Roteiro de defesa

---

## Pipeline de dados

Hoje `python/collectors/` só tem `config.yaml` (sem código) e `python/etl/` só tem `gerar_sinteticos.py` (entidades via Mockaroo). Nenhuma das etapas abaixo existe ainda. Numeração D.1–D.9 sincronizada com `docs/BACKLOG_E_GATES.md` — ver [ADR-011](adr/0011-estrategia-dados-reais-demonstracao.md) para a decisão de identificador/fornecedor em D.1 (confirmada contra o schema real da API do Compras.gov.br).

- [ ] D.1 — Coletor `compras_gov` (`python/collectors/compras_gov.py`) — itens de TI por CATMAT, `dataset/raw/compras_gov/<data>/*.json`, testes com fixtures em `tests/fixtures/` (sem rede)
- [ ] D.2 — Exportar 100 itens coletados no formato de `dataset/demo/inventario_demo.csv` e importar via `POST /importacoes` — libera o Gate 1
- [ ] D.3 — Coletor `endoflife` (`python/collectors/endoflife.py`) — ciclos de vida por produto, `dataset/raw/endoflife/<data>/*.json`, testes com fixtures
- [ ] D.4 — Coletor `nvd` (`python/collectors/nvd.py`) — CVEs por produto, `dataset/raw/nvd/<data>/*.json`, testes com fixtures
- [ ] D.5 — Gerar `dataset/synthetic/colaboradores.csv` via Mockaroo e versionar
- [ ] D.6 — Normalização (`python/etl/`) — `dataset/raw/` → `dataset/processed/`, classificando por CATMAT e cruzando software × ciclo de vida × CVE
- [ ] D.7 — Geração de eventos sintéticos (`python/etl/`) — transferências, baixas e instalações via `SYNTHETIC_SEED`, em `dataset/synthetic/` (distinto de `gerar_sinteticos.py`, que gera as entidades via Mockaroo)
- [ ] D.8 — Carga no banco — `dataset/processed/` + `dataset/synthetic/` → tabelas via ORM, com `data_source` por origem
- [ ] D.9 — Integração do `scripts/seed.sh` com `dataset/processed/` e `dataset/synthetic/` — hoje o script só roda `alembic upgrade head`

## Próximos passos (ordem sugerida)

- [ ] 1. Modelo `historico_transferencia` com índice único parcial (BR-007) e trigger de imutabilidade.
- [ ] 2. `POST /ativos/{id}/responsavel` (atribuição e transferência) e `GET /ativos/{id}/historico`.
- [ ] 3. `utils/depreciacao.py` como função pura com `Decimal` e `GET /ativos/{id}/depreciacao`.
- [ ] 4. Gerar a migração de Sprint 2 a partir desses modelos.
- [ ] 5. Testes `test_ac009_...` a `test_ac020_...` (FR-002, FR-003).

## Riscos do roadmap

- `app/models/historico.py`, `licenca.py`, `baixa.py`, `risco.py`, `recomendacao.py` e os serviços de Sprints 2–5 (`depreciacao_service.py`, `licenca_service.py`, `baixa_service.py`, etc.) ainda são placeholders vazios.
- O job de CI que exige 100% de cobertura em `utils/` e `services/` está vermelho hoje (93%) — normal enquanto `utils/depreciacao.py` e o resto de `services/` não são implementados, mas fica registrado para não ser confundido com regressão.
- Gate 1 não está formalmente liberado: falta demonstrar a importação de um arquivo real de 100 linhas via `POST /importacoes` (D.2), com relatório de aceitos/rejeitados — não só o teste sintético em `tests/integration/test_importacao.py`.