# Roadmap — ITAM

Snapshot de progresso contra os gates e sprints definidos em [`BACKLOG_E_GATES.md`](BACKLOG_E_GATES.md). Atualizar a cada gate liberado.

_Última atualização: 2026-10-02_

> Legenda: `[x]` concluído · `[ ]` pendente ou aguardando verificação. Observações após o travessão indicam o que ainda falta.

---

## Status por gate

| Gate | Tema | Status |
|---|---|---|
| Gate 0 | Enquadramento | Completo |
| Gate 1 | Inventário operacional | Aguardando liberação (importar arquivo real de 100 linhas) |
| Gate 2 | Responsabilidade e valor | Sprint 2 implementado; aguardando liberação (demonstração da linha do tempo com três transferências e conferência manual do residual) |
| Gate 3 | Conformidade e evento surpresa | Em andamento: baixa e licenças implementadas (Sprint 3); painel de compliance (FR-007) pendente |
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
- [x] AC-019 — resolvido na Sprint 3: `depreciacao_service` usa `baixa_ativo.data_baixa` e o valor residual congelado, verificado por `test_ac019_*` em `tests/integration/test_baixa.py`. O teste da função pura segue sem o prefixo `test_ac019`

## Sprint 3 — Licenças, baixas e compliance

Baixa (FR-005) e licenças (FR-004) implementadas em 2026-10-02. O painel de compliance (FR-007) continua pendente e fica para a Sprint 4.

- [x] Modelos `baixa_ativo` (`app/models/baixa.py`) e `licenca`, `licenca_vinculo` (`app/models/licenca.py`) — migrações `ee62f9bcb421` (baixa e trigger `tg_baixa_imutavel`) e `f5f9acc0de7b` (licenças, `ck_licenca_tipo` e índice parcial `ux_licenca_ativo`); `upgrade` → `downgrade` → `upgrade` e `alembic check` testados em PostgreSQL 16, e `upgrade` → `downgrade` → `upgrade` em SQLite
- [x] Serviços `baixa_service.py` e `licenca_service.py`; routers `POST /ativos/{id}/baixa` e `/licencas` (ver [`contrato-api.md`](spec/contrato-api.md) §6.4)
- [x] Baixa em transação única: status `BAIXADO`, vínculo de responsável encerrado (BR-012), valor residual congelado (BR-015); BR-022 a BR-026
- [x] Depreciação do ativo baixado pela `data_baixa` e pelo valor congelado (BR-015, AC-019) em `depreciacao_service.calcular_para_ativo`; `utils/depreciacao.py` não mudou
- [x] Licenças: `quantidade_em_uso` derivada por COUNT (BR-021, ADR-008), bloqueio de excedente (BR-018), licença vencida (BR-020), vigência (BR-019), desvínculo lógico (AC-026)
- [x] Mascaramento de `chave_licenca` (RI-08, `****-****-A3F9`; completa só no detalhe e só para ADMIN) em licenças **e** nas respostas de ativo (`app/utils/mascaramento.py`). Chave com menos de 8 caracteres sai toda mascarada
- [x] Recusas por regra gravam `RECUSADO` na auditoria com `regra` (NFR-AUD-05); recusa por concorrência provocada de verdade (BR-018 com lock na licença; BR-024 e `ux_licenca_ativo` com escritor externo)
- [x] ACs cobertos: AC-011, AC-019, AC-021, AC-024 a AC-030, AC-032 e AC-033 (mapa na seção "Decisões da Sprint 3" abaixo)
- [ ] **AC-022 e AC-023** — dependem do painel de compliance (FR-007, backlog 3.5 e 3.10): a licença traz `dias_para_expiracao`, mas `status_conformidade` e `alertas` (contrato §6.4) ainda não existem
- [ ] **AC-031** — "relatório de inventário ativo": o relatório é da Sprint 4 (FR-006). Hoje `GET /ativos?status=BAIXADO` já filtra por baixado, mas a listagem sem filtro devolve todos os status
- [ ] Regras CP-01 a CP-09 e `compliance_service.py` (vazio) — Sprint 4
- [ ] Contador `itam_regras_violadas_total` (`docs/spec/observabilidade.md`) nas recusas — depende de `core/metrics.py` (Sprint 4); as recusas já gravam `regra` na auditoria
- [ ] `ativo.produto_software_id` e as tabelas `produto_software`, `ativo_software`, `vulnerabilidade` — fora do escopo desta entrega
- [ ] Baixa de hardware com licenças vinculadas: os vínculos de licença **não** são desfeitos pela baixa (os docs só pedem encerrar o vínculo de responsável, BR-012). Decisão da equipe pendente, ver "Decisões da Sprint 3"

### Decisões da Sprint 3 (os docs não definiam; revisar com a equipe)

- **Permissões (ADR-013):** o contrato dizia `POST /ativos/{id}/baixa` e `PATCH`/`GET /licencas/{id}` só para ADMIN; a matriz do FR-015 permite a OPERADOR criar baixa e editar licença, e a todos lerem. Vale o PRD e o contrato foi corrigido. Se a equipe preferir ADMIN-only, é trocar uma linha em cada router
- **`data_source = manual`** em baixa, licença e vínculo criados pela API (item 8 da resolução do Sprint 2). Os docs diziam "sempre `sintetico`"
- **AC-024:** o texto fala em "data de aquisição" da licença, campo que saiu no item 4 da resolução. Vale a BR-019: expiração posterior ao início da vigência, também garantida por `ck_licenca_vigencia`
- **BR-022, BR-023, BR-026 e BR-019 como 409 com `regra`**, não 422 de schema: `destinacao` é opcional no schema e a justificativa de `OUTRO` é checada no serviço, para a recusa ter `regra` e ir à auditoria
- **BR-012 na data:** baixa com `data_baixa` anterior ao início do vínculo aberto é recusada com `regra = BR-012` (encerrar o vínculo antes de começar violaria `data_fim >= data_inicio`)
- **Vínculo de licença:** a máquina hospedeira precisa ser `HARDWARE`; a mesma máquina não pode ter dois vínculos ativos da mesma licença; ambos recusam com `regra = FR-004`. `data_vinculo` é opcional (padrão hoje) e não futura
- **`DELETE /licencas/{id}/vinculos/{ativo_id}`** é desvínculo lógico (`ativo_vinculo = false`), responde 204 e audita como `EXCLUIR`; `GET .../vinculos` devolve ativos e desvinculados
- **`PATCH /licencas/{id}`** edita fornecedor, chave, quantidade contratada e datas. Reduzir a quantidade abaixo do uso é recusado (BR-018). Tipo, ativo, `software` e `valor_total` não mudam
- **Mapa AC → teste:** AC-011 `test_responsavel_vinculo.py::test_ac011_*` · AC-019 `test_baixa.py::test_ac019_*` · AC-021 `test_licencas.py::test_ac021_*` · AC-024 `test_ac024_*` · AC-025 `test_ac025_*` · AC-026 `test_ac026_*` · AC-027 a AC-030, AC-032, AC-033 `test_baixa.py::test_ac0NN_*`

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
- [x] Cobertura ≥ 70% global / 100% em `utils` e `services` — verificado em 2026-10-02: 99,4% global e 100% em `utils/`+`services/` (314 testes contra PostgreSQL 16)
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
- [ ] D.9 — Integração do `scripts/seed.sh` com `dataset/processed/` e `dataset/synthetic/`. **Parcial (2026-10-02):** o seed já migra o banco e cria os quatro usuários de demonstração e as 11 categorias (`python/app/seed.py`, com testes em `tests/integration/test_seed.py`). Continua pendente a carga do pipeline (`processed/` e `synthetic/`, depende de D.8)

## Próximos passos (ordem sugerida)

- [x] 1. Equipe decide as contradições com a ADR-012 e o papel de `licenca` — resolvido (itens 2 a 7 da resolução).
- [x] 2. Equipe decide o arredondamento da depreciação — segue o PRD (item 1, ADR-013).
- [ ] 3. Liberar o Gate 2: demonstrar a linha do tempo de um ativo com três transferências e conferir o residual à mão.
- [x] 4. Fechar a cobertura de `ativo_service.py` e `importacao_service.py` — 100% em `utils/` + `services/`.
- [ ] 5. Preencher os papéis em `docs/guia/equipe-e-ia.md`.
- [x] 6. Sprint 3 — licenças (com `ck_licenca_tipo` e validação do ativo `SOFTWARE` no serviço) e baixas (com `data_baixa` na depreciação, AC-019). Falta a parte de compliance (FR-007, CP-01 a CP-09).

## Riscos do roadmap

- `app/models/risco.py`, `recomendacao.py` e os serviços das Sprints 4–5 (`compliance_service.py`, `indicador_service.py` etc.) ainda são placeholders vazios. Os de baixa e licença foram preenchidos na Sprint 3.
- **Pendências abertas pela resolução do Sprint 2** (decisões da equipe em 2026-09-30, ver [`RESOLUCAO_PENDENCIAS_SPRINT2.md`](RESOLUCAO_PENDENCIAS_SPRINT2.md)):
  - `produto_software` e `ativo_software` existem só na documentação, e a FK `ativo.produto_software_id` ainda não existe (fora do escopo da Sprint 3). `licenca`, `licenca_vinculo` e o `ck_licenca_tipo` entraram na migração `f5f9acc0de7b`;
  - `licenca.data_expiracao` continua `NOT NULL` também para licença perpétua ("prazo indeterminado"). Mantido por decisão da equipe (mudar alteraria BR-019); revisar no Sprint 3;
  - a validação "`licenca.ativo_id` aponta para ativo `SOFTWARE`" está em `licenca_service.criar_licenca` (409, `regra = FR-004`), porque o CHECK não enxerga outra tabela;
  - `POST /responsaveis` grava `data_source = sintetico` e `POST /fornecedores` aceita `data_source` enviado pelo cliente. A resolução do item 8 cobre só ativo e vínculo (decisão da equipe); baixa, licença e vínculo de licença, novos na Sprint 3, gravam `manual`;
  - `data_source` não tem `CHECK` no schema, embora `enumeracoes.md` diga que todo enum é `VARCHAR` com `CHECK`;
  - o `FR-003` do PRD mostra `depreciacao_acumulada = depreciacao_mensal × meses_efetivos`, sem dizer onde arredonda. O código segue a leitura aprovada no item 1 (arredondar só no fim); a redação da fórmula no PRD fica para a equipe;
  - **NFR-MAN-05** (PRD) e a premissa P6 do SPEC (`escopo-e-premissas.md`) diziam que os perfis SQLite e PostgreSQL "executam os mesmos testes". **Redação alinhada em 2026-10-02:** NFR-MAN-05, P6, ADR-007 e RI-10 marcados como revisados (item 13), sem renumerar, descrevendo o estado atual: o SQLite só executa a aplicação (verificado: migrações e fluxos de cadastro, transferência, depreciação e importação rodam em SQLite, sem trigger, lock de linha nem FK). A permanência do perfil SQLite segue como decisão da equipe;
  - `licenca.ck_licenca_tipo` é por tipo (PERPETUA → `ativo_id`; SUBSCRICAO → `software` + `valor_total`; OEM → `software`, sem valor), como a equipe confirmou em 2026-09-30;
  - a mensagem 409 genérica de `flush_ou_conflito` (cadastros sem BR) continua desfazendo a transação inteira, sem auditoria `RECUSADO`. Essas unicidades não são BR (item 11), então a NFR-AUD-05 não se aplica a elas.
