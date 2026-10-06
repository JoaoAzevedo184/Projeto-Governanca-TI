# Roadmap — ITAM

Snapshot de progresso contra os gates e sprints definidos em [`BACKLOG_E_GATES.md`](BACKLOG_E_GATES.md). Atualizar a cada gate liberado.

_Última atualização: 2026-10-05_

> Legenda: `[x]` concluído · `[ ]` pendente ou aguardando verificação. Observações após o travessão indicam o que ainda falta.

---

## Status por gate

| Gate | Tema | Status |
|---|---|---|
| Gate 0 | Enquadramento | Completo |
| Gate 1 | Inventário operacional | **Pronto para demonstrar** (ainda não liberado). Critério de liberação: arquivo de 100 linhas importado, 92 ativos e relatório de 8 erros. `dataset/demo/inventario_demo.csv` (100 linhas reais do Compras.gov.br, 92 válidas e 8 inválidas de propósito) importa com 100 processadas, 92 aceitas e 8 rejeitadas, provado por `tests/integration/test_gate1_inventario_demo.py` e rodado de verdade num banco descartável (seed, fornecedores, importação); falta a equipe fazer a demonstração |
| Gate 2 | Responsabilidade e valor | **Pronto para demonstrar** (ainda não liberado). Sprint 2 implementado; o seed de demonstração (`scripts/seed_demo.sh`) cria o ativo com atribuição inicial e três transferências e o ativo do AC-015 (residual R$ 4.800,00); roteiro em `docs/guia/demonstracao.md`. Falta a equipe demonstrar a linha do tempo e conferir o residual à mão |
| Gate 3 | Conformidade e evento surpresa | **Pronto para demonstrar** (ainda não liberado). Baixa e licenças (Sprint 3) e painel de compliance (Sprint 4) implementados; o seed de demonstração cria a licença em 50 de 50 (o 51º vínculo fica para a demonstração ao vivo), uma licença vencida há 40 dias, uma perto de vencer, um ativo baixado e exatamente 3 ativos sem responsável. Falta a equipe demonstrar e preparar o evento surpresa |
| Gate 4 | Decisão e defesa | Em andamento: decisão rastreável implementada (Sprint 5); falta demonstrar e o roteiro de defesa |

## Critérios de aceite da disciplina

| # | Critério | FR | Onde está | Situação |
|---|---|---|---|---|
| 1 | Cadastro válido com bloqueio de duplicidade por número de série ou chave de licença | FR-001 | Sprint 1 (BR-001, AC-002; BR-039, AC-067) | Implementado: número de série (BR-001, AC-002, AC-046) e chave de licença do ativo (BR-039, AC-067, índice `ux_ativo_chave_licenca`, decisão da equipe de 2026-10-05); falta demonstrar (Gate 1). A chave da licença (`licenca.chave_licenca`) continua sem unicidade, de propósito |
| 2 | Histórico de responsáveis append-only | FR-002 | Sprint 2 (trigger, AC-009 a AC-014) | Implementado; falta demonstrar (Gate 2) |
| 3 | Depreciação linear e valor residual automáticos | FR-003 | Sprint 2 (AC-015 a AC-020) | Implementado; falta conferência manual (Gate 2) |
| 4 | Alertas de licença excedente e próxima do vencimento | FR-004, FR-007 | Sprints 3 e 4 (CP-01 a CP-04, AC-021 a AC-023) | Implementado; falta demonstrar (Gate 3) |
| 5 | Baixa com motivo, data e destinação | FR-005 | Sprint 3 (BR-022 a BR-026, AC-027 a AC-033) | Implementado; falta demonstrar (Gate 3) |
| 6 | Importação CSV/XLSX com relatório de rejeitadas | FR-008 | Sprint 1 (AC-044 a AC-046) | Implementado; arquivo de 100 linhas pronto (`dataset/demo/inventario_demo.csv`: 100 processadas, 92 aceitas, 8 rejeitadas, provado em teste); falta demonstrar (Gate 1) |
| 7 | Indicadores reproduzíveis | FR-009 | Sprint 4 (AC-047) | Implementado; KPI-01, KPI-04 e KPI-05 fora do MVP |
| 8 | Cenários com TCO de cinco anos | FR-010 | Sprint 5 (AC-052) | Implementado; falta demonstrar (Gate 4) |
| 9 | Scorecard com pesos configuráveis | FR-011 | Sprint 5 (AC-048, AC-049) | Implementado; falta demonstrar (Gate 4) |
| 10 | Recomendação vinculada a evidências e riscos, sem decisão automática | FR-013 | Sprint 5 (BR-027, BR-028, AC-051) | Evidência implementada (`python/app/services/recomendacao_service.py:53-64`, BR-027, AC-051). Risco entra como evidência do tipo `RISCO`, opcional, com `referencia_id` validado contra `risco` (`recomendacao_service.py:27-28`; testes em `python/tests/integration/test_recomendacoes.py:85-141`). O PRD exige só ≥ 1 evidência de qualquer tipo (BR-027, `docs/prd/requisitos-funcionais.md:343`): nada obriga a citar um risco, e `evidencia.referencia_id` não tem FK |

## Itens do backlog e dos gates sem registro neste roadmap

- [ ] 5.8 Documentação final e checklist de entrega
- [ ] Gate 4: deploy funcionando (confirmar com o professor o que conta como deploy)
- [ ] Datasets liberados por gate: definir como entram no sistema (a importação só carrega ativos)
- [ ] Gate 3: preparação para o evento surpresa
- [ ] 4.4 Relatórios de depreciação, baixas e histórico (fora do MVP)
- [ ] Definition of Done: revisão por outro integrante dos itens das Sprints 3 a 5

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
- [x] Unicidade de chave de licença do ativo (BR-039, AC-067) — **decisão da equipe em 2026-10-05**: o critério 1 da disciplina exige bloqueio por chave de licença; unicidade só em `ativo.chave_licenca` (índice único parcial `ux_ativo_chave_licenca`, migração `d4a6c8e0f1b2`), não em `licenca.chave_licenca`, porque a renovação de subscrição pode repetir a chave. Recusa 409 `BR-039` com `RECUSADO` na auditoria, sem expor a chave (RI-08); a importação rejeita a linha. `PATCH /ativos` segue sem editar `numero_serie` nem `chave_licenca`. Corrida resolvida pelo índice (escritor externo: ETL, carga D.8)
- [x] Validações de data e valor (BR-003, BR-004 — via `model_validator`/`Field`, 422)
- [x] Herança de vida útil da categoria (BR-006, AC-007)
- [x] Pipeline de importação CSV/XLSX (pandas) — cabeçalho, duplicidade no arquivo e na base, isolamento por linha
- [x] `LoteImportacao` / `ErroImportacao`
- [x] Trilha de auditoria em toda escrita (`app/core/audit.py`, AC-057)
- [x] Handler global de erros com campo `regra` (`app/core/exceptions.py`, padrão RFC 7807 do SPEC)
- [x] Migração `13ade34ba8a3` (tabelas de Sprint 1) — aplicada e revertida
- [x] Cadastros de apoio (`/categorias` com `GET/PATCH /{id}`, `/fornecedores`, `/setores`, `/responsaveis`) — CRUD, 404, 422, unicidade (409, via `flush_ou_conflito`) e auditoria testados em `tests/integration/test_cadastros.py`
- [x] Matriz RBAC completa das rotas existentes (`tests/integration/test_seguranca.py`) — parametrizada pelos 4 perfis (ADMIN, OPERADOR, GESTOR, AUDITOR) × todas as rotas de `docs/spec/contrato-api.md` §6.2/6.3/6.6, mais um teste dedicado de "sem token → 401" em todas elas, inclusive `GET /auth/me`
- [x] `POST/PATCH` de categoria/fornecedor/setor/responsável agora registram auditoria (`app/services/{categoria,fornecedor,setor,responsavel}_service.py`) — antes só `ativo` registrava, violava AC-057/BR-030. **Correção de 2026-10-05:** a frase anterior dizia que a importação também registrava, mas `importacao_service.py` nunca chamou `registrar_auditoria` (o histórico do git não tem nenhuma versão que o fizesse). A importação passou a auditar em 2026-10-05, ver o item abaixo
- [x] Coluna opcional `data_source` na importação (2026-10-05, FR-008, AC-071; opção B do `DIAGNOSTICO_D2.md`): `compras_gov` ou `importacao` por linha; vazia ou ausente grava `importacao`; `manual` e qualquer outro valor viram erro de linha. Para `ativo`, os docs listam `compras_gov`, `importacao` e `manual` (`dicionario-de-dados.md`, `modelo-fisico.md`); `endoflife`, `nvd` e `sintetico` são de outras tabelas, então não são aceitos (decisão da equipe). A auditoria da linha CRIAR/ativo registra o `data_source` gravado. Sem `CHECK` no banco e sem mudar as outras rotas
- [x] Importação sem derrubar o arquivo (2026-10-05, FR-008, AC-068, AC-069): texto acima do tamanho da coluna (`nome`, `numero_serie`, `chave_licenca`, `localizacao`; limites lidos do modelo) e `valor_compra` com parte inteira acima de 10 dígitos, mais de 2 casas decimais ou não finito viram erro de linha, sem arredondar; antes, um único valor assim chegava ao banco e a resposta era `422` para o arquivo inteiro. O valor mostrado no relatório é cortado em 255 caracteres e a chave fica mascarada (RI-08). Testes `test_ac068_*` e `test_ac069_*` em CSV e XLSX
- [x] Corrida no número de série (2026-10-05, AC-070): conflito real no índice único de `ativo.numero_serie` (escritor externo: ETL, carga D.8) passou de `500` para `409` com `BR-001`, `RECUSADO` na auditoria e contador, como a `BR-039`. A importação em lote continua sem tratar esse conflito: uma corrida no índice durante o lote desfaz o lote inteiro (transação única) e sobe como erro
- [x] Importação em lote audita (2026-10-05, AC-057/BR-030): uma linha `CRIAR`/`ativo` por ativo aceito, com `lote_importacao_id` no `detalhe`, e uma linha `CRIAR`/`lote_importacao` com os totais, todas na mesma transação do lote (`app/services/importacao_service.py`). Linhas rejeitadas não geram auditoria de ativo. Testes `test_ac057_importacao_*` em `tests/integration/test_importacao.py`
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
- [x] **Resolução de pendências** ,  aprovada em 2026-09-30 — itens 0 a 15 aplicados:
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

Baixa (FR-005) e licenças (FR-004) implementadas em 2026-10-02. O painel de compliance (FR-007) foi entregue na Sprint 4.

- [x] Modelos `baixa_ativo` (`app/models/baixa.py`) e `licenca`, `licenca_vinculo` (`app/models/licenca.py`) — migrações `ee62f9bcb421` (baixa e trigger `tg_baixa_imutavel`) e `f5f9acc0de7b` (licenças, `ck_licenca_tipo` e índice parcial `ux_licenca_ativo`); `upgrade` → `downgrade` → `upgrade` e `alembic check` testados em PostgreSQL 16, e `upgrade` → `downgrade` → `upgrade` em SQLite
- [x] Serviços `baixa_service.py` e `licenca_service.py`; routers `POST /ativos/{id}/baixa` e `/licencas` (ver [`contrato-api.md`](spec/contrato-api.md) §6.4)
- [x] Baixa em transação única: status `BAIXADO`, vínculo de responsável encerrado (BR-012), valor residual congelado (BR-015); BR-022 a BR-026
- [x] Depreciação do ativo baixado pela `data_baixa` e pelo valor congelado (BR-015, AC-019) em `depreciacao_service.calcular_para_ativo`; `utils/depreciacao.py` não mudou
- [x] Licenças: `quantidade_em_uso` derivada por COUNT (BR-021, ADR-008), bloqueio de excedente (BR-018), licença vencida (BR-020), vigência (BR-019), desvínculo lógico (AC-026)
- [x] Mascaramento de `chave_licenca` (RI-08, `****-****-A3F9`; completa só no detalhe e só para ADMIN) em licenças **e** nas respostas de ativo (`app/utils/mascaramento.py`). Chave com menos de 8 caracteres sai toda mascarada
- [x] Recusas por regra gravam `RECUSADO` na auditoria com `regra` (NFR-AUD-05); recusa por concorrência provocada de verdade (BR-018 com lock na licença; BR-024 e `ux_licenca_ativo` com escritor externo)
- [x] ACs cobertos: AC-011, AC-019, AC-021, AC-024 a AC-030, AC-032, AC-033 e AC-058 a AC-064 (mapa na seção "Decisões da Sprint 3" abaixo)
- [x] **AC-022 e AC-023** — dependiam do painel de compliance (FR-007, backlog 3.5 e 3.10); entregues na Sprint 4 (`status_conformidade` e `alertas` da licença, `GET /compliance/alertas`)
- [x] **AC-031** — "relatório de inventário ativo": coberto na Sprint 4 por `GET /relatorios/inventario` (sem `status`, o baixado não aparece), teste `test_ac031_*` em `tests/integration/test_relatorios.py`
- [x] Regras CP-01 a CP-04 e `compliance_service.py` — Sprint 4 (AC-022, AC-023, AC-039 a AC-043). CP-05 a CP-09: ver FR-007 no PRD
- [x] Contador `itam_regras_violadas_total` (`docs/spec/observabilidade.md`) nas recusas — entregue na Sprint 4
- [ ] `ativo.produto_software_id` e as tabelas `produto_software`, `ativo_software`, `vulnerabilidade` — fora do escopo desta entrega
- [x] Baixa e vínculos de licença: resolvido depois da Sprint 3, com BR-031 (a baixa encerra os vínculos de licença da máquina), BR-036 e BR-037 (software baixado)

### Decisões da Sprint 3 (os docs não definiam; revisar com a equipe)

- **Permissões (ADR-013):** o contrato dizia `POST /ativos/{id}/baixa` e `PATCH`/`GET /licencas/{id}` só para ADMIN; a matriz do FR-015 permite a OPERADOR criar baixa e editar licença, e a todos lerem. Vale o PRD e o contrato foi corrigido. Se a equipe preferir ADMIN-only, é trocar uma linha em cada router
- **`data_source = manual`** em baixa, licença e vínculo criados pela API (item 8 da resolução do Sprint 2). Os docs diziam "sempre `sintetico`"
- **AC-024:** o texto fala em "data de aquisição" da licença, campo que saiu no item 4 da resolução. Vale a BR-019: expiração posterior ao início da vigência, também garantida por `ck_licenca_vigencia`
- **BR-022, BR-023, BR-026 e BR-019 como 409 com `regra`**, não 422 de schema: `destinacao` é opcional no schema e a justificativa de `OUTRO` é checada no serviço, para a recusa ter `regra` e ir à auditoria
- **BR-012 na data:** baixa com `data_baixa` anterior ao início do vínculo aberto é recusada com `regra = BR-012` (encerrar o vínculo antes de começar violaria `data_fim >= data_inicio`)
- **Vínculo de licença:** a máquina hospedeira precisa ser `HARDWARE`; a mesma máquina não pode ter dois vínculos ativos da mesma licença; as recusas usam `regra = BR-033` (não `HARDWARE`) e `BR-034` (vínculo duplicado); máquina `BAIXADO` recusa com `BR-032`, e a baixa encerra os vínculos de licença da máquina (`BR-031`). Licença cujo ativo `SOFTWARE` está baixado: a baixa do software encerra os vínculos da licença (`BR-036`) e a licença recusa vínculos novos com `BR-037`, derivado do status do ativo (sem migração); `BR-037` vem logo depois de `BR-032` na ordem de checagem. Eram `regra = FR-004` até 2026-10-02; FR é requisito, não regra. `data_vinculo` é opcional (padrão hoje) e não futura
- **`DELETE /licencas/{id}/vinculos/{ativo_id}`** é desvínculo lógico (`ativo_vinculo = false`), responde 204 e audita como `EXCLUIR`; `GET .../vinculos` devolve ativos e desvinculados
- **`PATCH /licencas/{id}`** edita fornecedor, chave, quantidade contratada e datas. Reduzir a quantidade abaixo do uso é recusado (BR-018). Tipo, ativo, `software` e `valor_total` não mudam
- **Mapa AC → teste:** AC-011 `test_responsavel_vinculo.py::test_ac011_*` · AC-019 `test_baixa.py::test_ac019_*` · AC-021 `test_licencas.py::test_ac021_*` · AC-024 `test_ac024_*` · AC-025 `test_ac025_*` · AC-026 `test_ac026_*` · AC-027 a AC-030, AC-032, AC-033 `test_baixa.py::test_ac0NN_*` · AC-058 a AC-064 `test_licencas.py::test_ac058_*` a `test_ac064_*`

## Sprint 4 — Indicadores, relatórios e observabilidade

Implementada em 2026-10-02. Ambiente completo (API, banco, Prometheus, Grafana) subido com Docker, seed e `scripts/smoke_test.sh` executados com sucesso.

- [x] Compliance (FR-007): `compliance_service.py`, `utils/conformidade.py`, `GET /compliance/alertas`; CP-01 a CP-04 (AC-022, AC-023, AC-039 a AC-043); `status_conformidade` e `alertas` no bloco derivado da licença
- [x] Relatórios (FR-006): `relatorio_service.py`, `utils/exportacao.py`, `GET /relatorios/inventario` e `/relatorios/conformidade` em JSON, CSV e XLSX (AC-031, AC-034 a AC-038)
- [x] Indicadores (FR-009): `indicador_service.py`, `utils/indicadores.py`, `GET /indicadores` (AC-047)
- [x] `/health` com banco e ambiente, `/metrics` no formato Prometheus (AC-053, AC-054); `core/metrics.py` com as métricas `itam_*` e o middleware HTTP
- [x] Contador `itam_regras_violadas_total` num único ponto, `registrar_auditoria`
- [x] Log estruturado JSON com `request_id`, sem dado sensível (`core/logging.py`)
- [x] Grafana provisionado: dashboard `itam-tecnico` na pasta **Governança de TI** (`infra/grafana/dashboards/`)
- [x] Pendências da sessão anterior: BR-038 (responsável e setor ativos, AC-065) e BR-037 ampliada para a criação de licença perpétua (AC-066)
- **Fora do MVP** (marcado nos docs, com o motivo de cada um): `/relatorios/depreciacao`, `/relatorios/baixas`, `/relatorios/historico-responsaveis` e o termo de responsabilidade (contrato §6.5, dashboard-relatorios §16.3); CP-05 a CP-09 (FR-007); KPI-01, KPI-04 e KPI-05 (visao-geral §4.3)
- Fora do MVP: CP-05, CP-06 e CP-08 (deriváveis, sem AC); CP-07 e CP-09 não disparam com o modelo atual; alertas MEDIO/BAIXO do FR-004 sem código CP. Ver FR-007 no PRD
- Fora do MVP: gráficos do painel gerencial (FR-014, PRD §16.2) e a evolução do valor residual no tempo: o contrato não tem endpoint para eles
- Fora do MVP: KPI-01, KPI-04 e KPI-05 do PRD, que não são calculáveis só com o banco (precisam de estimativa do parque, cronometragem e dado contábil)
- [x] `docker compose up` migra o banco ao iniciar o contêiner da API (`python/entrypoint.sh`); o seed segue separado
- [x] Recusa de inicialização com `SECRET_KEY` padrão fora de `local` (configuracao.md §13.1), em `core/config.py`; a chave do Compose vem do `.env`

### Decisões da Sprint 4 (os docs não definiam; revisar com a equipe)

- **Escopo de CP:** só CP-01 a CP-04 (os que têm AC). Sem alerta MEDIO/BAIXO de licença (saturada, subutilizada), que o FR-004 lista sem código CP.
- **`status_conformidade`:** `NAO_CONFORME` com CP-01 ou CP-02, `ALERTA` só com CP-03, `CONFORME` sem alertas. KPI-03 conta como não conforme só `NAO_CONFORME`.
- **Códigos dos indicadores:** `KPI-02`, `KPI-03`, `KPI-06`, `KPI-07`, `KPI-08` onde o PRD tem KPI; `IND-01` a `IND-07` nos demais indicadores do FR-009. Campos novos no contrato: `detalhe` (distribuições) e `sentido_meta`.
- **Indicadores:** patrimônio, custo médio, idade e ociosidade sobre ativos não baixados; custo médio divide pelo total de não baixados; período só afeta a taxa de baixas (padrão: 365 dias até hoje); a taxa de baixas conta no numerador toda baixa do período, mesmo de ativo adquirido depois do início do período, como a fórmula literal do PRD; filtro de setor pelo vínculo de responsável aberto; filtro de fornecedor também recorta licenças.
- **Inventário:** sem `status`, exclui `BAIXADO` (AC-031); filtros de depreciação e de fim de vida útil aplicados em Python sobre o resultado do SQL; chave de licença sempre mascarada no relatório.
- **Relatórios não pedidos no AC:** `depreciacao`, `baixas` e `historico-responsaveis` ficaram de fora.
- **Contador de recusas:** `registrar_auditoria`, quando `RECUSADO` com `regra_violada`. 422 e 403 não contam.
- **`/health` fora do ar:** `503` com `DOWN`. Métrica extra `itam_database_up`.
- **`/metrics` fora das métricas e do log**, para o scrape de 15 s não poluir.
- **`docker-compose.yml`:** `healthcheck` na API e Prometheus esperando a API saudável, como a ARQUITETURA §6 já descrevia.
- **Alembic:** `env.py` passou a `disable_existing_loggers=False`, para não silenciar o log da aplicação quando a migração roda no mesmo processo (testes).

## Sprint 5 — Decisão, qualidade e defesa

Implementada em 2026-10-03, exceto o roteiro de defesa e o pipeline de dados (fora desta entrega).

- [x] Riscos (FR-012): `models/risco.py`, `risco_service.py`, `utils/risco.py`, `/riscos` (AC-050); migração `a7c1e5d90b21`
- [x] Scorecard de fornecedores (FR-011): `models/fornecedor.py` (`FornecedorAvaliacao`), `scorecard_service.py`, `utils/scorecard.py`, `POST /fornecedores/scorecard` (AC-048, AC-049, BR-029); migração `b3d8f2a61c47`
- [x] Cenários e TCO (FR-010): `cenario_service.py`, `utils/cenario.py`, `POST /cenarios/comparar` (AC-052, BR-028). Só calculado, não persistido
- [x] Recomendação rastreável (FR-013): `models/recomendacao.py`, `recomendacao_service.py`, `/recomendacoes` (AC-051, BR-027); migração `c9e4a7d25f83`
- [x] Testes de contrato: schemathesis 4.10.2 sobre `api/openapi.yaml` em todas as operações (`tests/contract/test_contrato_schemathesis.py`), mais a sincronia do arquivo com o app
- [x] Cobertura ≥ 70% global / 100% em `utils` e `services`
- [x] `scripts/smoke_test.sh` — executado contra o ambiente completo
- [ ] Roteiro de defesa

### Decisões da Sprint 5 (os docs não definiam; revisar com a equipe)

- **409, não 422, em BR-027 e BR-029:** o contrato §6.7 dizia 422; vale o `padrao-de-erros.md` (regra de negócio = 409 com `regra`, auditada e contada). Contrato corrigido.
- **Permissões:** `GET /riscos/{id}` passa a ser de todos os perfis (FR-015); escrita em governança só ADMIN e GESTOR. A US-035 (Auditor registra riscos) perde para o AC-055.
- **Cenário só calculado:** sem tabela, sem auditoria. Entrada com `capex`, `opex_anual` e `riscos_ids`; baseline `MANTER` (ou o primeiro); ordem por TCO, score, nome; custo por ativo usa os ativos não baixados por padrão.
- **Contrato:** dinheiro como string no exemplo de cenários; o exemplo numérico contradizia o §6.
- **Evidência:** `INDICADOR`, `CENARIO` e `PREMISSA` não têm registro e levam `descricao` (sem `referencia_id`); `SCORECARD` aponta para o fornecedor; alerta de compliance não é tipo de evidência.
- **`status_risco`** (`ABERTO`, `EM_TRATAMENTO`, `ENCERRADO`) e **`periodo`** do scorecard (rótulo de texto) foram definidos aqui: os docs citam os campos sem os valores.
- **Recomendação sem edição:** o contrato não tem `PATCH`; o status é o informado ao registrar. Faltaria um endpoint de transição (proposta → aprovada → implementada) para a decisão avançar no sistema.
- **Scorecard sem `UNIQUE`:** reavaliar o mesmo período acrescenta linhas. Empate de pontuação desempata pelo menor id.
- **Doc corrigido:** `0.3 + 0.3 + 0.4 != 1.0` (regras-de-calculo §7.4) é falso em Python; o exemplo passou a `0.1 + 0.2 != 0.3`.
- **Pesos do scorecard da demonstração (escolha da equipe):** o FR-011 sugere os critérios (preço, prazo de entrega, qualidade do suporte, taxa de defeitos, aderência contratual) mas não fixa pesos. Para a demonstração do Gate 4 a equipe aprovou 30/15/25/15/15 (soma 100, BR-029), em `app/seed_demo.py` (`PESOS_SCORECARD`). Não é regra do sistema: a API aceita quaisquer pesos que somem 100.

### Achados dos testes de contrato (Sprint 5)

- **Corrigido, 500 → 422:** id maior que 32 bits na rota ou no corpo (`/ativos/99999999999`) estourava o driver (`NumericValueOutOfRange`) e virava 500. Um handler de `DataError` devolve 422 sem a mensagem do driver.
- **Corrigido, fora do formato:** token ausente, corpo ilegível, rota inexistente e método não permitido saíam como `{"detail": ...}`; agora saem no formato único (`/erros/http-<status>`).
- **Corrigido, contrato incompleto:** o `openapi.yaml` só documentava 200/201/422 e o 422 como `HTTPValidationError`, que a API não devolve. Agora toda rota documenta 400, 401, 403, 404, 409 e 422 com `ErroResponse`; os relatórios documentam `text/csv` e XLSX.
- **Não corrigido:** a validação do Pydantic é permissiva e aceita `0` como booleano e números como texto onde o schema diz boolean; o schemathesis acusa (`negative_data_rejection`). Modo estrito quebraria a entrada de dinheiro como string. Check desligado no teste, achado registrado aqui.
- **Não corrigido:** `positive_data_acceptance` desligado, porque uma API de regras recusa com 404/409 dados válidos pelo schema (id inexistente, série duplicada).
- **Sem 500 residual** nas 45 operações com 10 exemplos cada, semente fixa.

---

## Pipeline de dados

Hoje `python/collectors/` tem o coletor `compras_gov` (D.1) e `config.yaml`, e `python/etl/` só tem `gerar_sinteticos.py` (entidades via Mockaroo). As demais etapas abaixo ainda não existem. Numeração D.1–D.9 sincronizada com `docs/BACKLOG_E_GATES.md` — ver [ADR-011](adr/0011-estrategia-dados-reais-demonstracao.md) para a decisão de identificador/fornecedor em D.1 (confirmada contra o schema real da API do Compras.gov.br).

- [x] D.1 — Coletor `compras_gov` (`python/collectors/compras_gov.py`) — itens de TI por CATMAT, `dataset/raw/compras_gov/<data>/*.json`, testes com fixtures em `tests/fixtures/` (sem rede). **Concluído em 2026-10-05:** `python -m collectors.compras_gov` coleta os PDMs de `config.yaml` com paginação, novas tentativas com espera crescente, intervalo entre requisições e gravação atômica (sem arquivo pela metade; rodar de novo no mesmo dia pula o que já está completo); 27 testes em `tests/unit/test_compras_gov.py` com respostas reais gravadas em `tests/fixtures/compras_gov/` (ver `ORIGEM.md`). **Divergências a confirmar pela equipe:** usa `/modulo-pesquisa-preco/1_consultarMaterial`, não o `modulo-legado/2_consultarItemLicitacao` da ADR-011 (o legado não traz preço pago nem data da compra); a lista de 9 PDMs em `config.yaml` é provisória (sem Nobreak nem Smartphone). Diagnóstico do que o D.2 exige: `graphify-out/DIAGNOSTICO_D2.md`
- [x] D.2 — Arquivo do Gate 1: `python/etl/exportar_inventario_demo.py` gera `dataset/demo/inventario_demo.csv` (100 linhas: 92 válidas e 8 inválidas de propósito, coluna `erro_proposital`), `fornecedores_demo.csv` e `inventario_demo.LEIAME.md` (metodologia, números por filtro e por PDM) a partir de `dataset/raw/compras_gov/2026-10-05/`; `python/etl/carregar_fornecedores.py` carrega os 17 fornecedores via `POST /fornecedores` (`data_source = compras_gov`, idempotente, credenciais por ambiente). **Concluído em 2026-10-05:** `tests/integration/test_gate1_inventario_demo.py` exige 100 processadas, 92 aceitas, 8 rejeitadas (linha e campo exatos), 92 ativos `compras_gov` e 93 linhas de auditoria (92 ativos e 1 lote). `numero_serie = CG-{idItemCompra}-001` é identificador técnico sintético (ADR-011, atualização de 2026-10-05). A seleção usa 17 fornecedores, não ~10: com 10 só saem 73 linhas (decisão da equipe)
- [ ] D.3 — Coletor `endoflife` (`python/collectors/endoflife.py`) — ciclos de vida por produto, `dataset/raw/endoflife/<data>/*.json`, testes com fixtures
- [ ] D.4 — Coletor `nvd` (`python/collectors/nvd.py`) — CVEs por produto, `dataset/raw/nvd/<data>/*.json`, testes com fixtures
- [ ] D.5 — Gerar `dataset/synthetic/colaboradores.csv` via Mockaroo e versionar **Substituído pelo seed de demonstração (`python -m app.seed_demo`), a confirmar pela equipe:** para a demonstração dos Gates 2 e 3 o seed cobre o que este item previa; o item segue aberto.
- [ ] D.6 — Normalização (`python/etl/`) — `dataset/raw/` → `dataset/processed/`, classificando por CATMAT e cruzando software × ciclo de vida × CVE
- [ ] D.7 — Geração de eventos sintéticos (`python/etl/`) — transferências, baixas e instalações via `SYNTHETIC_SEED`, em `dataset/synthetic/` (distinto de `gerar_sinteticos.py`, que gera as entidades via Mockaroo) **Substituído pelo seed de demonstração (`python -m app.seed_demo`), a confirmar pela equipe:** para a demonstração dos Gates 2 e 3 o seed cobre o que este item previa; o item segue aberto.
- [ ] D.8 — Carga no banco — `dataset/processed/` + `dataset/synthetic/` → tabelas via ORM, com `data_source` por origem **Substituído pelo seed de demonstração (`python -m app.seed_demo`), a confirmar pela equipe:** para a demonstração dos Gates 2 e 3 o seed cobre o que este item previa; o item segue aberto.
- [ ] D.9 — Integração do `scripts/seed.sh` com `dataset/processed/` e `dataset/synthetic/`. **Parcial (2026-10-02):** o seed já migra o banco e cria os quatro usuários de demonstração e as 11 categorias (`python/app/seed.py`, com testes em `tests/integration/test_seed.py`). Continua pendente a carga do pipeline (`processed/` e `synthetic/`, depende de D.8) **Substituído pelo seed de demonstração (`python -m app.seed_demo`), a confirmar pela equipe:** para a demonstração dos Gates 2 e 3 o seed cobre o que este item previa; o item segue aberto.
- [x] Seed de demonstração dos Gates 2 e 3 (2026-10-05): `python -m app.seed_demo` (`scripts/seed_demo.sh`, `python/app/seed_demo.py`). Roda dentro da aplicação, chamando os services (nada de SQL direto nem de HTTP; regra de negócio, trigger e auditoria valem), e cria só registros `sintetico` com identificadores `DEMO-`: 3 setores, 6 responsáveis, 1 fornecedor, responsável para 89 dos 92 ativos reais (3 ficam sem, de propósito), o ativo das 3 transferências, o ativo do AC-015, o software com licença de 50 unidades e 50 vínculos (o 51º fica para a demonstração ao vivo), uma licença vencida há 40 dias, uma a vencer e um ativo baixado. Idempotente; exige o seed básico e os 92 ativos importados; recusa `ENVIRONMENT=producao`. A origem é parâmetro interno dos services (padrão `manual`; `sintetico` no responsável), fora dos schemas e do contrato. Testes em `tests/integration/test_seed_demo.py`. Decisão: o seed cobre, para a demonstração, o que D.5, D.7, D.8 e D.9 previam; **substituição a confirmar pela equipe**, os itens seguem abertos

## Próximos passos (ordem sugerida)

- [x] 1. Equipe decide as contradições com a ADR-012 e o papel de `licenca` — resolvido (itens 2 a 7 da resolução).
- [x] 2. Equipe decide o arredondamento da depreciação — segue o PRD (item 1, ADR-013).
- [ ] 3. Liberar o Gate 2: demonstrar a linha do tempo de um ativo com três transferências e conferir o residual à mão.
- [x] 4. Fechar a cobertura de `ativo_service.py` e `importacao_service.py` — 100% em `utils/` + `services/`.
- [ ] 5. Preencher os papéis em `docs/guia/equipe-e-ia.md`.
- [x] 6. Sprint 3 — licenças (com `ck_licenca_tipo` e validação do ativo `SOFTWARE` no serviço) e baixas (com `data_baixa` na depreciação, AC-019).

## Correções encontradas no ambiente Docker (2026-10-05)

- [x] **Login utilizável no Swagger:** o esquema de segurança passou de OAuth2 (fluxo de senha, que enviava formulário a `/auth/login` e recebia 422) para **HTTP Bearer**: o Authorize mostra um campo de token. Login e respostas iguais; sem token ou com token inválido segue 401 no formato do projeto (`python/app/api/deps.py`). `api/openapi.yaml` só mudou nos esquemas de segurança. Verificado num navegador de verdade: login pelo Try it out, token no Authorize, `GET /auth/me` com 200. Testes em `tests/integration/test_swagger_bearer.py`. Fluxo no README e em `docs/guia/demonstracao.md`
- [x] **Microempreendedores fora do arquivo de demonstração:** o exportador (`python/etl/exportar_inventario_demo.py`) descarta fornecedores cuja razão social é o nome de uma pessoa física (`64.956.713 NOME` ou nome + 11 dígitos); 61 dos 702 registros federais. A coleta bruta e as fixtures não foram alteradas. O arquivo segue com 100 linhas (92 válidas, 8 inválidas), 9 PDMs e agora 17 fornecedores. **Decisão de LGPD pendente:** 6 razões sociais (8 registros) da coleta, em `dataset/raw/` e nas fixtures versionadas, trazem um número de 11 dígitos (possível CPF); nada foi apagado
- [x] **Data de referência no fuso de Recife:** "hoje" do domínio (`app/utils/datas.hoje()`) usa `FUSO_HORARIO`, padrão `America/Recife`; em UTC o dia virava às 21h locais. Vale para data futura (BR-003 e as outras datas "não futuras"), licença vencida, janela de alerta e depreciação. Carimbos de tempo e demais regras não mudaram. Testes com relógio controlado em `tests/unit/test_fuso_da_data_de_referencia.py` e `tests/integration/test_data_de_referencia.py`. Verificado dentro da imagem Docker: a base de fusos já está na `python:3.12-slim`, sem dependência nova. Fora da correção, por não serem "hoje" do domínio: `agora()` do cabeçalho dos relatórios exportados (`relatorio_service.py`), a pasta datada da coleta (`collectors/compras_gov.py`) e o `iat`/`exp` do JWT (UTC)
- **Pendente (sem alteração de código):** `total_rejeitado` de `POST /importacoes` conta **erros por campo**, não linhas rejeitadas (`importacao_service.py:269,278`), então um arquivo de 100 linhas pode devolver `total_rejeitado: 106`; o PRD (FR-008, AC-044) fala em registros e linhas inválidas. Opções no relatório da sessão

## Riscos do roadmap

- **Pendência de alinhamento entre PRD, contrato e código (2026-10-05):** (1) o PRD diz que o contrato de licença é `sintetico` (`docs/prd/requisitos-funcionais.md`, FR-004, "Origem dos dados"), mas `POST /licencas` grava `manual`; (2) `FornecedorCreate` expõe `data_source` ao cliente (`python/app/schemas/fornecedor.py`), enquanto a decisão de 2026-10-05 é que a origem não faz parte dos schemas nem do contrato HTTP. Nenhuma das duas foi corrigida; a equipe decide qual lado muda.

- **Carga D.8 e auditoria (BR-030):** a carga D.8 grava via ORM (`dataset/processed/` e `dataset/synthetic/` → tabelas) e não passa pelos services, então não grava `audit_log`. A importação pela API (`POST /importacoes`) audita desde 2026-10-05, mas a carga externa não. A equipe precisa decidir se a BR-030 vale para carga externa; se valer, a carga terá de chamar `registrar_auditoria` ou passar pelos services.
- **Pendências abertas pela resolução do Sprint 2** (decisões da equipe em 2026-09-30, ver `RESOLUCAO_PENDENCIAS_SPRINT2.md`):
  - `produto_software` e `ativo_software` existem só na documentação, e a FK `ativo.produto_software_id` ainda não existe (fora do escopo da Sprint 3). `licenca`, `licenca_vinculo` e o `ck_licenca_tipo` entraram na migração `f5f9acc0de7b`;
  - `licenca.data_expiracao` continua `NOT NULL` também para licença perpétua ("prazo indeterminado"). Mantido por decisão da equipe (mudar alteraria BR-019); revisar no Sprint 3;
  - a validação "`licenca.ativo_id` aponta para ativo `SOFTWARE`" está em `licenca_service.criar_licenca` (409, `regra = BR-035`, antes `FR-004`), porque o CHECK não enxerga outra tabela;
  - `POST /responsaveis` grava `data_source = sintetico` e `POST /fornecedores` aceita `data_source` enviado pelo cliente. A resolução do item 8 cobre só ativo e vínculo (decisão da equipe); baixa, licença e vínculo de licença, novos na Sprint 3, gravam `manual`;
  - `data_source` não tem `CHECK` no schema, embora `enumeracoes.md` diga que todo enum é `VARCHAR` com `CHECK`;
  - o `FR-003` do PRD mostra `depreciacao_acumulada = depreciacao_mensal × meses_efetivos`, sem dizer onde arredonda. O código segue a leitura aprovada no item 1 (arredondar só no fim); a redação da fórmula no PRD fica para a equipe;
  - **NFR-MAN-05** (PRD) e a premissa P6 do SPEC (`escopo-e-premissas.md`) diziam que os perfis SQLite e PostgreSQL "executam os mesmos testes". **Redação alinhada em 2026-10-02:** NFR-MAN-05, P6, ADR-007 e RI-10 marcados como revisados (item 13), sem renumerar, descrevendo o estado atual: o SQLite só executa a aplicação (verificado: migrações e fluxos de cadastro, transferência, depreciação e importação rodam em SQLite, sem trigger, lock de linha nem FK). A permanência do perfil SQLite segue como decisão da equipe;
  - **Limitação conhecida do MVP — baixa retroativa:** `licenca_vinculo` não tem datas próprias além de `data_vinculo` (sem data de fim), então uma baixa com `data_baixa` retroativa pode ficar anterior à criação de um vínculo de licença que ela encerra (BR-031, BR-036). O encerramento só aparece no carimbo da auditoria. Não há regra para isso (diferente do BR-012, que protege o vínculo de responsável); datas no vínculo de licença ficam para depois do MVP;
  - `licenca.ck_licenca_tipo` é por tipo (PERPETUA → `ativo_id`; SUBSCRICAO → `software` + `valor_total`; OEM → `software`, sem valor), como a equipe confirmou em 2026-09-30;
  - a mensagem 409 genérica de `flush_ou_conflito` (cadastros sem BR) continua desfazendo a transação inteira, sem auditoria `RECUSADO`. Essas unicidades não são BR (item 11), então a NFR-AUD-05 não se aplica a elas.
