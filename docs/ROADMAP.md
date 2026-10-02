# Roadmap — ITAM

Snapshot de progresso contra os gates e sprints definidos em [`BACKLOG_E_GATES.md`](BACKLOG_E_GATES.md). Atualizar a cada gate liberado.

_Última atualização: 2026-09-30_

> Legenda: `[x]` concluído · `[ ]` pendente ou aguardando verificação. Observações após o travessão indicam o que ainda falta.

---

## Status por gate

| Gate | Tema | Status |
|---|---|---|
| Gate 0 | Enquadramento | Completo |
| Gate 1 | Inventário operacional | Aguardando liberação (importar arquivo real de 100 linhas) |
| Gate 2 | Responsabilidade e valor | Sprint 2 implementado; aguardando liberação (demonstração da linha do tempo com três transferências e conferência manual do residual) |
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

- [x] ADR-012 — software é Ativo, resolve QA-06 ([`adr/0012-software-como-ativo.md`](adr/0012-software-como-ativo.md))
- [x] Modelo `historico_transferencia` (`app/models/historico.py`) — índice único parcial `ux_vinculo_aberto` (BR-007) e trigger `permitir_apenas_encerramento` no PostgreSQL (BR-011/BR-025): só a transição de `data_fim` de nulo para preenchido é aceita, a opção (a) de `docs/modelo-de-dados/invariantes.md` (ADR-005)
- [x] Transferência em `app/services/responsavel_service.py`, junto do CRUD do Sprint 1, como prevê `docs/spec/estrutura-diretorios.md` — lock no ativo, encerra o vínculo aberto e cria o novo na mesma transação; recusas 409 com `regra` (BR-008, BR-009, BR-010, FR-002 para responsável/setor inativo) registradas na auditoria
- [x] `utils/depreciacao.py` — função pura com `Decimal` e `ROUND_HALF_UP`, sem ramo por tipo de ativo (ADR-012)
- [x] `app/services/depreciacao_service.py`
- [x] Endpoints `GET /ativos/{id}/depreciacao`, `GET /ativos/{id}/historico` e `POST /ativos/{id}/responsavel`, na matriz RBAC e no teste "sem token → 401"
- [x] Bloco `depreciacao` na resposta de `POST/GET/PATCH /ativos` (AC-018)
- [x] Migração `c8365ce7e5e4` (tabela, índice parcial e trigger) — `upgrade` → `downgrade` → `upgrade` e `alembic check` testados em SQLite e em PostgreSQL 16
- [x] `api/openapi.yaml` regenerado a partir do app (também cobre as rotas do Sprint 1, que ainda estavam em `paths: {}`)
- [x] Testes AC-009 a AC-020 — AC-013 testado no banco (trigger) e na API (nenhuma rota de edição/exclusão)
- [x] **Resolução de pendências** ([`RESOLUCAO_PENDENCIAS_SPRINT2.md`](RESOLUCAO_PENDENCIAS_SPRINT2.md), aprovada em 2026-09-30) — itens 0 a 15 aplicados:
  - ADR-013: PRD prevalece em regra de negócio, SPEC em implementação (item 0);
  - depreciação arredonda só no resultado final, `valor × meses ÷ vida_útil`; a mensal é informativa (item 1, AC-020 passa a 2.000,00);
  - subscrição e OEM não são ativo; nota de amortização no glossário (itens 2 e 3);
  - `licenca` passa a ser só o contrato de uso; `licenca_vinculo.ativo_id` é a máquina hospedeira; `produto_software` é catálogo; `ativo_software` continua separada (itens 4 a 6, só docs; tabelas implementadas no Sprint 3);
  - jornada §8.2 reescrita e QA-06 marcada como resolvida (item 7);
  - `data_source = manual` para `POST /ativos` e para o vínculo (item 8);
  - dinheiro como string no contrato; trigger e unicidades documentados (itens 9 a 11);
  - recusa BR-007 por concorrência grava `RECUSADO` na auditoria via savepoint (item 12, ver abaixo);
  - suíte inteira em PostgreSQL 16, local e CI; schema via `alembic upgrade head` (item 13);
  - cobertura de `utils/` + `services/` em 100% (item 14);
  - testes revisados contra os critérios anti falso positivo (item 15).
- [x] Recusa por concorrência com auditoria (NFR-AUD-05). **Só um escritor externo provoca o conflito** (ETL, carga D.8). Pela API, as transferências travam o ativo e se serializam. Com o lock antigo (`FOR UPDATE`), nem o escritor externo o provocava: a FK do insert externo toma `KEY SHARE` no ativo, e a transferência esperava no lock e respondia 201. O lock passou a `FOR NO KEY UPDATE`. Teste com conflito real em `test_br007_conflito_real_no_indice_grava_recusa_na_auditoria`
- [ ] AC-019 só no nível da função pura — o serviço usa a data corrente para todo ativo; trocar por `baixa_ativo.data_baixa` quando a baixa existir (Sprint 3). O teste da função pura perdeu o prefixo `test_ac019`, porque o critério em si ainda não é verificável

## Sprint 3 — Licenças, baixas e compliance

- [ ] Modelos `licenca`, `baixa_ativo` — vazios
- [ ] Serviços de licença, baixa e compliance — `licenca_service.py`, `baixa_service.py`, `compliance_service.py` vazios
- [ ] Endpoints correspondentes
- [ ] Regras CP-01 a CP-09
- [ ] Mascaramento de `chave_licenca` em listagens (RI-08, `****-****-A3F9`, completa só no detalhe e só para ADMIN) — adiado do Sprint 1, natural aqui por tratar do módulo de licenças
- [ ] Depreciação do ativo baixado pela `data_baixa` (BR-015, AC-019) em `depreciacao_service.calcular_para_ativo`
- **Observação — impacto da ADR-012 em `licenca`:** com software patrimonial em `ativo`, `licenca` não pode registrar valor patrimonial de novo. Antes de modelar `licenca`, a equipe decide:
  - se `licenca` vira só o contrato de direito de uso (quantidade, vigência, CP-01 a CP-03) apontando para o ativo `SOFTWARE`;
  - o que fazer com `software`, `chave_licenca`, `data_aquisicao` e `valor_total`, que duplicam o ativo;
  - se `licenca_vinculo.ativo_id` é a máquina onde o software está instalado ou o próprio ativo `SOFTWARE` (o diagrama ER diz só "instala").

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
- [ ] Cobertura ≥ 70% global / 100% em `utils` e `services` — hoje: 97% global (passa), 95% no escopo `utils+services`. Os arquivos novos do Sprint 2 estão em 100% (`utils/depreciacao.py`, `depreciacao_service.py`, `responsavel_service.py`), assim como os cadastros; faltam `ativo_service.py` (96%) e `importacao_service.py` (86%), ambos do Sprint 1. O job "Cobertura de 100% em utils/ e services/" do CI **continua falhando**: verificado em 2026-09-29, "total of 95 is less than fail-under=100"
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

- [x] 1. Equipe decide as contradições com a ADR-012 e o papel de `licenca` — resolvido (itens 2 a 7 da resolução).
- [x] 2. Equipe decide o arredondamento da depreciação — segue o PRD (item 1, ADR-013).
- [ ] 3. Liberar o Gate 2: demonstrar a linha do tempo de um ativo com três transferências e conferir o residual à mão.
- [x] 4. Fechar a cobertura de `ativo_service.py` e `importacao_service.py` — 100% em `utils/` + `services/`.
- [ ] 5. Preencher os papéis em `docs/guia/equipe-e-ia.md`.
- [ ] 6. Sprint 3 — licenças (com `ck_licenca_tipo` e FK para o ativo `SOFTWARE`), baixas (com `data_baixa` na depreciação, AC-019) e compliance.

## Riscos do roadmap

- `app/models/licenca.py`, `baixa.py`, `risco.py`, `recomendacao.py` e os serviços de Sprints 3–5 (`licenca_service.py`, `baixa_service.py` etc.) ainda são placeholders vazios.
- **Pendências abertas pela resolução do Sprint 2** (decisões da equipe em 2026-09-30, ver [`RESOLUCAO_PENDENCIAS_SPRINT2.md`](RESOLUCAO_PENDENCIAS_SPRINT2.md)):
  - `produto_software`, `ativo_software`, `licenca` e `licenca_vinculo` existem só na documentação. A FK `ativo.produto_software_id` e o `ck_licenca_tipo` entram na migração do Sprint 3;
  - `licenca.data_expiracao` continua `NOT NULL` também para licença perpétua ("prazo indeterminado"). Mantido por decisão da equipe (mudar alteraria BR-019); revisar no Sprint 3;
  - a validação "`licenca.ativo_id` aponta para ativo `SOFTWARE`" fica no serviço de licenças, porque o CHECK não enxerga outra tabela;
  - `POST /responsaveis` grava `data_source = sintetico` e `POST /fornecedores` aceita `data_source` enviado pelo cliente. A resolução do item 8 cobre só ativo e vínculo (decisão da equipe);
  - `data_source` não tem `CHECK` no schema, embora `enumeracoes.md` diga que todo enum é `VARCHAR` com `CHECK`;
  - o `FR-003` do PRD mostra `depreciacao_acumulada = depreciacao_mensal × meses_efetivos`, sem dizer onde arredonda. O código segue a leitura aprovada no item 1 (arredondar só no fim); a redação da fórmula no PRD fica para a equipe;
  - **NFR-MAN-05** (PRD) e a premissa P6 do SPEC (`escopo-e-premissas.md`) dizem que os perfis SQLite e PostgreSQL "executam os mesmos testes". O item 13 tirou o SQLite dos testes, então a redação do NFR contradiz a resolução. Não foi editada: a equipe decide se o perfil SQLite continua existindo só para executar a aplicação;
  - `licenca.ck_licenca_tipo` é por tipo (PERPETUA → `ativo_id`; SUBSCRICAO → `software` + `valor_total`; OEM → `software`, sem valor), como a equipe confirmou em 2026-09-30;
  - a mensagem 409 genérica de `flush_ou_conflito` (cadastros sem BR) continua desfazendo a transação inteira, sem auditoria `RECUSADO`. Essas unicidades não são BR (item 11), então a NFR-AUD-05 não se aplica a elas.
