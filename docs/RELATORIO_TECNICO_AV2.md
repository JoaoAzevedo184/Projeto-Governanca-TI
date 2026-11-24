# Relatório Técnico — 2ª Avaliação (AV2)

**Projeto:** ITAM — Gestão de Ativos de TI
**Disciplina:** Governança de TI — Sistemas de Informação — UNINASSAU Olinda
**Repositório:** `Projeto-Governanca-TI`
**Data de corte deste relatório:** [A EQUIPE PREENCHE: data da entrega da 2ª AV]. Os números abaixo foram medidos em 2026-11-23, sobre o commit `d6583d8` mais as alterações listadas na seção 5, versionadas no mesmo dia nos commits `5db2b3a` a `59d5da7`. O CI do `59d5da7` passou (run 45274407153).

> **Como ler este relatório.** O [Relatório da AV1](RELATORIO_TECNICO_AV1.md) descreve a baseline recebida, o que entrou e o que saiu. Este relatório trata da entrega: o ambiente em que o sistema roda, os números medidos e a evidência de cada critério da rubrica do ITAM (`material_aluno/RUBRICA.md`). Cada número vem de um comando executado em 2026-11-23, citado ao lado. Onde falta evidência, o texto traz `[A EQUIPE PREENCHE]`.

---

## 1. Ambiente entregue e números medidos

### 1.1 O ambiente é a entrega

A entrega roda com Docker Compose na máquina local. O professor confirmou que esse deploy local conta como deploy do Gate 4. Não há ambiente em nuvem.

Um único `docker compose up -d` sobe 4 serviços (`docker-compose.yml`):

| Serviço | Imagem | Papel |
|---|---|---|
| `api` | construída de `python/Dockerfile` (Python 3.12, FastAPI) | API REST, `/health`, `/metrics` e Swagger em `/docs`; roda `alembic upgrade head` ao iniciar |
| `db` | `postgres:16` | Banco da aplicação (`itam`) e banco da suíte (`itam_test`, criado por `infra/postgres/init/01-banco-de-teste.sql`) |
| `prometheus` | `prom/prometheus:v3.5.0` | Coleta `/metrics` da API a cada 15 s |
| `grafana` | `grafana/grafana:12.1.0` | Dashboards `itam-tecnico` e `itam-gestao`, provisionados na pasta **Governança de TI** |

As quatro portas publicadas no host vêm do `.env` (`API_PORT`, `DB_PORT`, `PROMETHEUS_PORT`, `GRAFANA_PORT`), com os padrões 8000, 5432, 9090 e 3000. A API fala com o banco pela rede interna (`db:5432`), sem depender de `DB_PORT`. Fora de `ENVIRONMENT=local`, a API recusa iniciar com `SECRET_KEY` vazia ou de exemplo.

Preparo completo, do banco vazio à demonstração: `docs/guia/preparo-da-demonstracao.md`.

### 1.2 Números medidos em 2026-11-23

| Medida | Resultado | Comando |
|---|---|---|
| Suíte completa | **1012 passed, 0 falhas**, 2 warnings, em 787,76 s | `pytest --cov=app --cov=api --cov=collectors --cov=etl` em `python/`, contra PostgreSQL 16 (`itam_test`) |
| Cobertura de `app/` (portão do CI ≥ 70%) | **99,90%** (3061 linhas, 3 sem cobertura) | `coverage report --include="app/*"` |
| Cobertura de `app/utils/` + `app/services/` (portão do CI = 100%) | **100%** (1239 linhas) | `coverage report --include="app/utils/*,app/services/*"` |
| Cobertura com coletores e ETL | 98,18% (3954 linhas, 72 sem cobertura; `etl/gerar_sinteticos.py` 0% e `etl/sanitizar_coleta.py` 42%) | `coverage report` |
| Testes com identificador de critério | **194 testes `test_ac`**, cobrindo **71 de 71** critérios distintos (AC-001 a AC-071) | `pytest --collect-only -q` |
| Lint | `ruff check .`: sem achados | `ruff check .` |
| Tipos | `mypy app`: sem erros em 89 arquivos | `mypy app --ignore-missing-imports` |
| Segurança estática | `bandit -r app -ll`: 0 achados de severidade média ou alta | `bandit -r app -ll` |
| Ambiente completo | **`smoke test OK`**: `/health` com banco UP, login, 5 rotas de negócio, `/metrics`, alvo do Prometheus UP e os 2 dashboards no Grafana | `docker compose up -d --build` e `scripts/smoke_test.sh` |
| CI no GitHub Actions | **success** no commit `59d5da7` (HEAD de `main`), em 2026-11-23 às 21:54 UTC, com 9 min 45 s | [run 45274407153](https://github.com/JoaoAzevedo184/Projeto-Governanca-TI/actions/runs/45274407153) |
| Cenário de demonstração num banco novo | Os 6 números do roteiro conferem (tabela 1.3) | Banco descartável `itam_demo_check`: migração, seed básico, fornecedores, importação e `python -m app.seed_demo` |

A verificação usou `DB_PORT=55432` e `API_PORT=18000`, porque as portas 5432 e 8000 da máquina estavam ocupadas por outro projeto (ver o achado 4.3).

### 1.3 Cenário de demonstração

Banco novo, semeado em 2026-11-23. A importação aceitou 92 ativos, e o `seed_demo` criou `3 setores, 6 responsaveis, 3 fornecedores, 4 ativos_demo, 95 vinculos_responsavel, 3 licencas, 50 vinculos_licenca, 1 baixas, 2 riscos, 3 avaliacoes, 1 recomendacoes`.

| O roteiro pede | Medido |
|---|---|
| Residual R$ 4.800,00 no ativo do Gate 2 (`DEMO-HW-AC015`) | Aquisição em 2025-11-23, residual `4800.00` |
| 1 licença vencida há 40 dias | `DEMO-LIC-VENCIDA-0040`, expirada em 2026-10-14 (−40 dias), alerta CP-01 `CRITICO` |
| 1 licença a menos de 30 dias do vencimento | `DEMO-LIC-A-VENCER-0025`, expira em 2026-12-18 (25 dias), alerta CP-03 `ALTO` |
| 1 licença em 50 de 50 | `DEMO-LIC-PERPETUA-0050`, 50 vínculos de 50 contratados |
| 3 ativos sem responsável | 3 alertas CP-04 `ALTO` |
| 1 ativo baixado | 1 ativo `BAIXADO` (`DEMO-HW-BAIXA`) |

Total de alertas: 5 (1 crítico e 4 altos), os mesmos números de `docs/guia/demonstracao.md`.

---

## 2. Demonstração funcional

A rubrica limita a nota a 70 sem demonstração funcional. A demonstração é ao vivo, sobre o ambiente da seção 1, conforme `docs/ROTEIRO_DEFESA.md` (5 minutos, 7 blocos).

| Gate | Critério de liberação | Situação em 2026-11-23 |
|---|---|---|
| Gate 1 | 100 linhas importadas, 92 ativos e relatório de 8 erros | Pronto para demonstrar; provado por `test_gate1_importa_100_linhas_92_aceitas_e_8_rejeitadas` |
| Gate 2 | Linha do tempo com 3 transferências e residual conferido à mão | Pronto para demonstrar; residual 4.800,00 medido num banco novo (tabela 1.3) |
| Gate 3 | 51º vínculo bloqueado com BR-018 e auditado | Pronto para demonstrar; `test_gate3_licenca_em_50_de_50_e_o_51o_vinculo_e_recusado_com_br018` |
| Gate 4 | Recomendação aberta, com cada evidência, e deploy funcionando | Pronto para demonstrar; deploy local com `smoke test OK` |

Nenhum gate foi formalmente liberado. Cada gate só é liberado depois que a equipe demonstra. [A EQUIPE PREENCHE: data e resultado de cada demonstração.]

**Pré-voo** (`ROTEIRO_DEFESA.md`, "Antes de entrar na sala"): portas livres ou ajustadas pelo `.env`, banco recriado no dia e os 6 números conferidos por `scripts/verificar_demo.sh`. **Plano B:** segunda máquina com o ambiente no ar e semeado no mesmo dia; gravação de tela do roteiro completo como último recurso. O perfil SQLite não é plano B (achado 4.1).

---

## 3. Testes de integridade, pelos critérios da rubrica

Uma linha de evidência por critério da rubrica do ITAM, a segunda das duas rubricas de `material_aluno/RUBRICA.md` (a primeira é a do Projeto 3, mantida no arquivo do professor). Todos os testes citados passaram na execução de 2026-11-23 (1012 passed).

| Critério (pontos) | Evidência |
|---|---|
| **Gestão e modelagem de ativos** (20) | AC-001 a AC-008 e AC-067 com teste, da duplicidade por número de série (`test_ac002_recusa_numero_serie_duplicado`) à busca parcial (`test_ac008_busca_por_numero_serie_parcial`), mais a importação real do Gate 1 com 100 linhas, 92 aceitas e 8 rejeitadas linha a linha (`tests/integration/test_gate1_inventario_demo.py`). |
| **Conformidade, ciclo de vida e rastreabilidade** (20) | Histórico append-only garantido no banco pelo trigger `permitir_apenas_encerramento` (`test_ac013_vinculo_encerrado_nao_admite_edicao_nem_exclusao`, em PostgreSQL), `audit_log` que recusa UPDATE e DELETE (`test_nfr_aud_01_audit_log_recusa_update_e_delete`), baixa com motivo, data e destinação (AC-027 a AC-033) e alertas CP-01 a CP-04 com a regra e o link de origem (AC-040 a AC-043). |
| **Indicadores, riscos e recomendações** (20) | Cada indicador traz fórmula e amostra (`test_ac047_cada_indicador_traz_formula_e_tamanho_da_amostra`), risco 4 × 5 sai score 20 e `CRITICO` (`test_ac050_probabilidade_4_e_impacto_5_dao_score_20_e_classificacao_critico`), e recomendação sem evidência é recusada com a BR-027 na auditoria e na métrica (`test_ac051_recomendacao_sem_evidencia_e_recusada_com_a_regra_na_auditoria_e_na_metrica`). |
| **TCO, depreciação e análise de cenários** (15) | Depreciação de R$ 6.000,00 em 60 meses após 12 meses dá residual 4.800,00 (`test_ac015_depreciacao_de_6000_em_60_meses_apos_12_meses`, e conferido num banco novo na tabela 1.3); cenários ordenados por TCO de 5 anos e risco, sem escolha automática (`test_ac052_cenarios_ordenados_por_custo_e_risco_e_nenhum_escolhido`). |
| **Governança, segurança e controle de acesso** (15) | Matriz RBAC dos 4 perfis testada rota a rota (`test_matriz_rbac_por_perfil` e `test_matriz_rbac_sem_token_retorna_401` em `test_seguranca.py`), API que recusa iniciar com `SECRET_KEY` de exemplo fora do ambiente local (`test_aplicacao_com_chave_padrao_e_environment_docker_se_recusa_a_iniciar`) e `bandit` sem achados médios ou altos. |
| **Produto, PoC e defesa** (10) | Ambiente completo no ar com `scripts/smoke_test.sh` → `smoke test OK` (seção 1.2), cenário dos 4 gates semeado e conferido num banco novo (tabela 1.3) e roteiro de 5 minutos com plano B em `docs/ROTEIRO_DEFESA.md`. |

**Tetos da rubrica.** "Sem demonstração funcional, teto 70": coberto pela demonstração ao vivo da seção 2. "Sem rastreabilidade das decisões e evidências, teto 80": a recomendação do Gate 4 tem 4 evidências tipadas (risco, scorecard, indicador e cenário), e toda escrita e toda recusa têm linha no `audit_log` imutável.

---

## 4. Achados desta verificação

### 4.1 O perfil SQLite não executa as migrações até o fim

Reproduzido nesta verificação, em 2026-11-23, num banco SQLite descartável (`DATABASE_URL=sqlite:///... alembic upgrade head`): a migração para em `python/alembic/versions/a7c1e5d90b21_sprint_5_risco.py`, com `sqlite3.OperationalError: near "(": syntax error`. A causa é `server_default=sa.text('now()')`, que o SQLite não aceita. O mesmo padrão está em `b3d8f2a61c47` e `c9e4a7d25f83`. É a falha 05 do `REGISTRO_USO_DE_IA.md`, corrigida na época só em `c8365ce7e5e4`.

**Decisão da equipe (2026-11-23):** não corrigir para a defesa. Mesmo com a migração corrigida, o SQLite não tem o trigger de imutabilidade, o lock de linha nem as FKs, que são o que a demonstração mostra. O RI-10 (execução sem Docker) fica, na prática, restrito às tabelas até a Sprint 3.

### 4.2 O cenário de demonstração fica preso ao dia em que foi semeado

O `seed_demo` calcula as datas a partir de `hoje()` (`app/utils/datas.py`) e grava os registros. Por ser idempotente, rodar de novo no mesmo banco não refaz as datas. O banco `itam` desta máquina foi semeado em 2026-10-06. Medido em 2026-11-23 pela API do ambiente no ar:

- `GET /api/v1/ativos/94/depreciacao` (`DEMO-HW-AC015`): 13 meses decorridos, e não 12, e residual `4700.00`, e não `4800.00`;
- `GET /api/v1/compliance/alertas`: 5 alertas, mas **2 críticos e 3 altos**, e não 1 e 4. As duas licenças de subscrição saem como CP-01 vencidas, porque `DEMO-LIC-A-VENCER-0025` expirou em 2026-10-31;
- `GET /api/v1/indicadores`: KPI-03 em `33.33`%, e não 2 de 3 conformes.

O código está certo, e os testes do seed conferem os números no dia da execução. A correção é operacional: **recriar o banco e semear no dia da apresentação**, nas duas máquinas do plano B. O passo está no `ROTEIRO_DEFESA.md` ("Antes de entrar na sala", item 1) e no `CHECKLIST_ENTREGA.md` (seção 3).

### 4.3 Portas ocupadas na máquina

As portas 5432 e 8000 estavam ocupadas por outro projeto. As quatro portas publicadas passaram a vir do `.env`, sem editar o `docker-compose.yml` (`docs/guia/execucao-local.md`, seção "Portas publicadas pelo Docker Compose"). A verificação desta seção rodou com `DB_PORT=55432` e `API_PORT=18000`.

---

## 5. Alterações desta etapa

Versionadas em 2026-11-23 e enviadas ao `origin/main`. O CI do último commit passou (run 45274407153).

| Arquivo | Alteração | Commit |
|---|---|---|
| `docker-compose.yml`, `.env.example`, `scripts/smoke_test.sh` | Portas publicadas parametrizadas (`API_PORT`, `DB_PORT`, `PROMETHEUS_PORT`, `GRAFANA_PORT`) | `5db2b3a` |
| `docs/guia/execucao-local.md`, `docs/guia/solucao-de-problemas.md` | Seção sobre portas e diagnóstico de porta ocupada | `5db2b3a` |
| `python/tests/integration/test_ativos.py` | `test_ac008_busca_por_numero_serie_parcial` (AC-008) | `9b00035` |
| `scripts/verificar_demo.sh` | Confere pela API os 6 números do cenário de demonstração (✓/✗ por item, código 1 se algum divergir); documentado em `docs/guia/preparo-da-demonstracao.md`, passo 8 | `11525c2` |
| `docs/RELATORIO_TECNICO_AV1.md`, `docs/RELATORIO_TECNICO_AV2.md`, `docs/ROTEIRO_DEFESA.md`, `docs/CHECKLIST_ENTREGA.md` | Documentos novos da entrega | `f06195b` |
| `docs/ROADMAP.md`, `docs/REGISTRO_USO_DE_IA.md` | Estado atual e registro das sessões de IA | `923672b`, `43239d8` |
| `python/requirements.txt` | Versões exatas de `pydantic` e `starlette`, dependências transitivas que mudavam de versão no CI e quebravam o `test_openapi_sincronizado` | `59d5da7` |

---

## 6. Pendências antes da apresentação

A lista completa, com a frente responsável por cada item, está em `docs/CHECKLIST_ENTREGA.md`. As que afetam a nota:

- Recriar o banco e semear **no dia** da apresentação, nas duas máquinas (achado 4.2).
- Gravação de tela do roteiro completo, feita na véspera num banco recém-semeado (plano B3).
- Conferência manual do residual do Gate 2 por quem não escreveu o código.
- Ensaio cronometrado do roteiro com as 5 pessoas.
