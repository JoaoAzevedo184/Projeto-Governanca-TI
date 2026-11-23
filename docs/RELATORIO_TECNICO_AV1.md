# Relatório Técnico — 1ª Avaliação (AV1)

**Projeto:** ITAM — Gestão de Ativos de TI
**Disciplina:** Governança de TI — Sistemas de Informação — UNINASSAU Olinda
**Repositório:** `Projeto-Governanca-TI`
**Data de corte deste relatório:** [A EQUIPE PREENCHE: data da entrega da 1ª AV]. As atividades registradas vão de 2026-09-02, data do primeiro commit, a 2026-10-06, data do último commit antes desta revisão (`d6583d8`).

> **Como ler este relatório.** O enunciado da 1ª AV pressupõe que a equipe recebeu um aplicativo pronto e o ajustou. O caso deste grupo é diferente: a baseline recebida foi o **Projeto 3 — Observabilidade e Operação Híbrida** do guia de orquestração da disciplina. Em 2026-09-22 a equipe trocou o domínio para Gestão de Ativos de TI (ITAM), um projeto novo construído sobre a stack e a estrutura dessa baseline. As seções abaixo seguem os itens do enunciado e fazem essa tradução explicitamente: "app disponibilizado" é a baseline do Projeto 3, e "app ajustado" é o ITAM.
>
> Todo número citado vem de um arquivo do repositório ou de um comando executado em 2026-11-23 (ver o [Relatório da AV2](RELATORIO_TECNICO_AV2.md), seção 1). Onde falta evidência, o texto traz `[A EQUIPE PREENCHE]`.

---

## 1. Avaliação geral do App disponibilizado

### 1.1 O que a baseline entregava

A baseline está no commit `64e9e18` (2026-09-02, "first commit"). Em seguida, o commit `deabe82` (mesmo dia) removeu as referências à implementação Java. O conteúdo verificado no histórico do git é o seguinte:

| Componente | O que havia | Evidência |
|---|---|---|
| Domínio | Observabilidade híbrida (datacenter, filiais e cloud): MTTD/MTTR, ruído e duplicidade de alertas, acionabilidade, SLI/SLO e error budget, owner e runbook, custo de telemetria, recomendação de tuning | `git show 64e9e18:spec.md` |
| API | Um único arquivo `python/app/main.py` (cerca de 50 linhas) em FastAPI, com 8 rotas: `/health`, `/metrics`, `POST /api/v1/imports/events`, `GET /api/v1/kpis`, `POST/GET /api/v1/slos`, `POST /api/v1/costs/compare` e `POST /api/v1/tuning/recommendations` | `git show deabe82:python/app/main.py` |
| Persistência | **Nenhuma.** O estado ficava em listas em memória (`events=[];slos=[];risks=[]`), e reiniciar a API zerava tudo. Não havia banco, ORM nem migração | `deabe82:python/app/main.py`, README da baseline ("O estado é mantido em memória") |
| Importação | Leitura de CSV com `csv.reader`, tolerante a BOM e a preâmbulo. Não validava campos nem gerava relatório de erros | `rows_from_csv` em `deabe82:python/app/main.py` |
| Recomendação | `POST /tuning/recommendations` exigia uma lista `evidence` com pelo menos 1 item (`Field(min_length=1)`), com status fixo `PROPOSED` | idem |
| Observabilidade | Contador `observability_http_requests_total`, `/metrics` no formato Prometheus, Prometheus v3.5.0 e Grafana 12.1.0 com provisionamento de datasource | `deabe82:docker-compose.yml`, `infra/` |
| Orquestração | `docker-compose.yml` com 3 serviços: API, Prometheus e Grafana | `deabe82:docker-compose.yml` |
| Testes | 1 arquivo, `python/tests/test_api.py` | `git show --stat 64e9e18` |
| Segurança | Sem autenticação, sem perfis de acesso e sem trilha de auditoria | `deabe82:python/app/main.py` |
| Dados | 5 CSV sintéticos do Projeto 3: `alertas.csv` (500 eventos), `slos.csv`, `custos.csv`, `riscos.csv` e `dashboard_referencia.csv` | `git show --stat 64e9e18` |
| Documentação | `spec.md` (39 linhas), e `ARQUITETURA.md`, `BACKLOG_E_GATES.md`, `CRITERIOS_DE_ACEITE.md` e `MODELO_DE_DADOS.md` com 5 a 12 linhas cada; rubrica, checklist e guia do aluno do Projeto 3 | idem |

### 1.2 Avaliação crítica da equipe

**O que serviu e foi mantido:**

- **A stack** (Python 3.12, FastAPI, Pydantic, Prometheus e Grafana nas mesmas versões de imagem, v3.5.0 e 12.1.0). Ela coincide com a stack que o guia do aluno do ITAM pede (`material_aluno/GUIA_DO_ALUNO.md`).
- **O padrão `/health` + `/metrics` + Grafana provisionado.** Virou o FR-014 e os AC-053 e AC-054.
- **A ideia de recomendação que exige evidência.** Virou o FR-013 e a BR-027, agora com evidência tipada, persistida e auditada.
- **A comparação de custos entre alternativas.** Virou o FR-010, com TCO de cinco anos e sem escolha automática (BR-028).
- **O registro de riscos.** Virou o FR-012, com score probabilidade × impacto (AC-050).

**O que não serviu para ITAM:**

- **Estado em memória.** Um sistema de ativos precisa de histórico imutável (NFR-AUD-01) e de trilha de auditoria. Isso exige banco relacional com restrições, por isso entraram PostgreSQL 16, SQLAlchemy e Alembic.
- **Importação sem validação.** O FR-008 exige relatório de rejeitadas com linha, campo e motivo (AC-044), e recusa de cabeçalho divergente antes de processar (AC-045).
- **Ausência de autenticação.** O FR-015 exige JWT e 4 perfis (ADMIN, OPERADOR, GESTOR, AUDITOR).
- **Todo o domínio de observabilidade** (MTTD/MTTR, SLO e error budget, runbook, custo de telemetria). Nada disso é requisito de ITAM; ver a seção 2.
- **Arquivo único sem camadas.** Não comportava regra de negócio testável isoladamente. A arquitetura passou a ter `api`, `services` e `utils` (funções puras), conforme a ADR-001 (monólito modular) em `docs/spec/adrs-e-rastreabilidade.md:9`.

---

## 2. Decisão sobre ajustes — inclusões e exclusões

### 2.1 Excluído

| Item da baseline ou do enunciado | Decisão | Justificativa | Sustentação |
|---|---|---|---|
| MTTD, MTTR, taxa de incidentes | Excluído | Métricas de operação de monitoramento, não de ativo | `git show 45f402e --stat`: `alertas.csv` removido |
| Ruído, duplicidade e acionabilidade de alertas | Excluído | Domínio de alert engineering. A duplicidade em ITAM é a de número de série e chave de licença (BR-001, BR-039) | `45f402e` |
| SLI, SLO e error budget | Excluído | Sem correspondente em gestão de ativos | `45f402e`: `slos.csv` removido |
| Owner e runbook de alerta crítico | Substituído | Em ITAM, o "dono" é o **responsável pelo ativo**, com histórico append-only (FR-002) | FR-002, BR-007, BR-011 |
| Custo de telemetria e comparação self-managed / SaaS / híbrido | Substituído | Virou o TCO de cinco anos entre alternativas de ativo (FR-010) | `45f402e`: `custos.csv` → `custos_cenarios.csv` |
| Dashboard executivo de observabilidade | Substituído | Virou o painel gerencial de ativos `itam-gestao` (FR-014) | `infra/grafana/dashboards/itam-gestao.json` |
| Service Desk e abertura de chamados (incluindo métricas de atendimento como FCR, CSAT, SLA e reabertura) | Fora de escopo | Coberto pelo Projeto 1 da baseline da disciplina | `docs/prd/escopo.md:38` (OUT-06) |
| Implementação dual Python + Java | Excluído | Entrega só em Python, aceita pelo professor. As referências a Java saíram da baseline em `deabe82` | `deabe82`; RE-01 e RI-05 em `docs/prd/planejamento.md` |
| Estado em memória | Excluído | Incompatível com histórico imutável e auditoria | NFR-AUD-01, ADR-005 |

### 2.2 Incluído

| Item | Justificativa | Requisito |
|---|---|---|
| Cadastro de ativos com unicidade de número de série e de chave de licença | Critério 1 da disciplina; base do inventário | FR-001, BR-001, BR-039, AC-001 a AC-008, AC-067 |
| Responsáveis com histórico append-only | Critério 2; o responsável atual é derivado do histórico, não de uma coluna (ADR-003) | FR-002, BR-007 a BR-011, AC-009 a AC-014 |
| Depreciação linear e valor residual | Critério 3; calculada sob demanda, não persistida (ADR-002) | FR-003, BR-013 a BR-017, AC-015 a AC-020 |
| Licenças com bloqueio de excedente e vencimento | Critério 4 | FR-004, BR-018 a BR-021, AC-021 a AC-026 |
| Baixa com motivo, data e destinação | Critério 5; congela o valor residual (BR-015) | FR-005, BR-022 a BR-026, AC-027 a AC-033 |
| Relatório de inventário e de conformidade | Consulta e exportação CSV/XLSX | FR-006, AC-031, AC-034 a AC-038 |
| Painel de compliance | Alertas CP-01 a CP-04 agrupados por severidade | FR-007, AC-039 a AC-043 |
| Importação CSV/XLSX com relatório de rejeitadas | Critério 6 | FR-008, AC-044 a AC-046, AC-068 a AC-071 |
| Indicadores com fórmula e amostra | Critério 7 | FR-009, AC-047 |
| Cenários com TCO de cinco anos | Critério 8 | FR-010, BR-028, AC-052 |
| Scorecard de fornecedores | Critério 9 | FR-011, BR-029, AC-048, AC-049 |
| Registro de riscos | Base da recomendação | FR-012, AC-050 |
| Recomendação rastreável | Critério 10; sem evidência, é recusada | FR-013, BR-027, AC-051 |
| Dashboard e observabilidade da própria API | Herdado da baseline e ampliado | FR-014, AC-053, AC-054 |
| Autenticação JWT e RBAC com 4 perfis | Ausente na baseline | FR-015, AC-055, AC-056 |
| Trilha de auditoria imutável, inclusive das tentativas recusadas | Exigida para governança | NFR-AUD-01, NFR-AUD-05, AC-057 |
| PostgreSQL 16, SQLAlchemy e Alembic | Restrições no banco (trigger, índice único parcial) | ADR-005, ADR-006 |

Os critérios 1 a 10 estão em `docs/CRITERIOS_DE_ACEITE.md`, e a situação de cada um está em `docs/ROADMAP.md:21-34`.

---

## 3. Produção dos artefatos necessários

Contagem feita com `find <dir> -maxdepth 1 -type f` em 2026-11-23.

| Artefato | Arquivos | Propósito |
|---|---|---|
| `docs/prd/` | 14 | PRD dividido por responsabilidade: visão, personas, escopo (IN-/OUT-), histórias (US-), FR-001 a FR-015, regras (BR-), 71 critérios de aceite (AC-001 a AC-071), NFR-, modelo conceitual, fluxos, dashboard, planejamento (RI-, RE-, QA-) e anexos (matriz de aderência a frameworks) |
| `docs/spec/` | 16 | Especificação técnica: arquitetura, stack, contrato da API, padrão de erros, modelo físico, regras de cálculo, pipeline de importação, segurança, observabilidade, configuração, estratégia de testes, plano de sprints e ADR-001 a ADR-010 resumidas (`adrs-e-rastreabilidade.md`) |
| `docs/modelo-de-dados/` | 10 | Diagrama ER, dicionário de dados, enumerações, índices, invariantes, migrações, dados semente, datasets de demonstração e consultas de referência |
| `docs/adr/` | 3 | ADR-011 (dados reais na demonstração), ADR-012 (software como ativo) e ADR-013 (o PRD prevalece em regra de negócio, o SPEC em implementação). As ADR-001 a ADR-010 estão em `docs/spec/adrs-e-rastreabilidade.md:9-18` |
| `docs/guia/` | 12, mais 1 em `exemplos/` | Execução local, testes, importação, coleta de dados, demonstração, preparo da demonstração, scripts operacionais, verificação, solução de problemas, contribuição, equipe e IA; `exemplos/cenarios_gate4.json` |
| `docs/ARQUITETURA.md` | 1 | Decisões de arquitetura D1 a D5, módulos, perfis de execução |
| `docs/BACKLOG_E_GATES.md` | 1 | Gates 0 a 4, backlog por sprint, Definition of Done, roteiro de defesa |
| `docs/ROADMAP.md` | 1 | Progresso por gate e sprint, decisões de cada sprint, riscos |
| `docs/FONTES_DE_DADOS.md` | 1 | Fontes públicas (Compras.gov.br, endoflife.date, NVD) e política LGPD |
| `docs/REGISTRO_USO_DE_IA.md` | 1 | 39 entradas de uso de IA com nível de revisão (R1 a R3) e 41 falhas encontradas em saídas de IA |
| `docs/CRITERIOS_DE_ACEITE.md` | 1 | Os 10 critérios de aceite da disciplina |
| **Total em `docs/`** | **62** | Antes dos 4 documentos produzidos em 2026-11-23 |

Fora de `docs/`, os artefatos de código e orquestração são:

- `python/app/`: 89 arquivos-fonte verificados pelo `mypy`.
- `python/alembic/versions/`: migrações.
- `python/api/openapi.yaml`: contrato congelado.
- `python/collectors/` e `python/etl/`: pipeline de dados.
- `docker-compose.yml` e `infra/`: Prometheus e os 2 dashboards Grafana.
- `scripts/`: 7 scripts operacionais.
- `.github/workflows/ci.yml`: CI com portões de cobertura.

**Achado do inventário.** 16 arquivos de `docs/` linkavam `RESOLUCAO_PENDENCIAS_SPRINT2.md`, que nunca entrou no git (nenhum commit do arquivo em `git log --all`). Resolvido em 2026-11-23: cada link foi trocado pela decisão do item citado e por um link para a seção da Sprint 2 do `ROADMAP.md`, onde os itens 0 a 15 estão resumidos (`REGISTRO_USO_DE_IA.md`, entrada 43). O `docs/ROADMAP.md:218` cita `graphify-out/DIAGNOSTICO_D2.md`, que também não está versionado. [A EQUIPE PREENCHE: restaurar o `DIAGNOSTICO_D2.md` ou remover a citação.]

---

## 4. Avaliação geral do App ajustado

### 4.1 Situação por requisito

Extraída do `docs/ROADMAP.md` (seções por sprint e "Critérios de aceite da disciplina"):

| FR | Requisito | Situação | Critérios | Onde |
|---|---|---|---|---|
| FR-001 | Cadastro de ativos | Implementado | AC-001 a AC-008, AC-067 | Sprint 1; `ROADMAP.md:58-81` |
| FR-002 | Vinculação de responsável | Implementado (trigger `permitir_apenas_encerramento`, índice `ux_vinculo_aberto`) | AC-009 a AC-014, AC-065 | Sprint 2; `ROADMAP.md:89-90` |
| FR-003 | Depreciação | Implementado, sob demanda (ADR-002) | AC-015 a AC-020 | Sprint 2; `ROADMAP.md:91-94` |
| FR-004 | Licenças | Implementado | AC-021 a AC-026, AC-058 a AC-064, AC-066 | Sprint 3; `ROADMAP.md:117-123` |
| FR-005 | Baixa | Implementado | AC-027 a AC-033 | Sprint 3; `ROADMAP.md:119-120` |
| FR-006 | Relatórios | Inventário e conformidade implementados; depreciação, baixas e histórico fora do MVP | AC-031, AC-034 a AC-038 | Sprint 4; `ROADMAP.md:149,156` |
| FR-007 | Compliance | CP-01 a CP-04 implementados; CP-05 a CP-09 fora do MVP | AC-022, AC-023, AC-039 a AC-043 | Sprint 4; `ROADMAP.md:148,157` |
| FR-008 | Importação | Implementado | AC-044 a AC-046, AC-068 a AC-071 | Sprint 1; `ROADMAP.md:70,78-81` |
| FR-009 | Indicadores | Implementado; KPI-01, KPI-04 e KPI-05 fora do MVP | AC-047 | Sprint 4; `ROADMAP.md:150,159` |
| FR-010 | Cenários e TCO | Implementado, só calculado | AC-052 | Sprint 5; `ROADMAP.md:183` |
| FR-011 | Scorecard | Implementado | AC-048, AC-049 | Sprint 5; `ROADMAP.md:182` |
| FR-012 | Riscos | Implementado | AC-050 | Sprint 5; `ROADMAP.md:181` |
| FR-013 | Recomendação rastreável | Implementado | AC-051 | Sprint 5; `ROADMAP.md:184` |
| FR-014 | Dashboard e observabilidade | Implementado: `/health`, `/metrics`, dashboards `itam-tecnico` e `itam-gestao` | AC-053, AC-054 | Sprint 4 e Gate 4; `ROADMAP.md:151-158` |
| FR-015 | Autenticação e RBAC | Implementado, matriz testada nos 4 perfis | AC-055, AC-056 | Sprint 1; `ROADMAP.md:63-64,76` |

### 4.2 Fora do MVP, por decisão registrada

| Item | Motivo | Registro |
|---|---|---|
| CP-05, CP-06 e CP-08 | Deriváveis, sem critério de aceite | `ROADMAP.md:157`, FR-007 no PRD |
| CP-07 e CP-09 | Não disparam com o modelo atual | idem |
| KPI-01, KPI-04 e KPI-05 | Não calculáveis só com o banco: precisam de estimativa do parque, cronometragem e dado contábil | `ROADMAP.md:159` |
| `/relatorios/depreciacao`, `/relatorios/baixas`, `/relatorios/historico-responsaveis` e termo de responsabilidade | Sem critério de aceite no PRD | `ROADMAP.md:156,170` (backlog 4.4) |
| Gráficos servidos pela própria API | O painel gerencial foi feito no Grafana | `ROADMAP.md:158` |
| `produto_software`, `ativo_software`, `vulnerabilidade` | Fora do escopo desta entrega | `ROADMAP.md:129` |
| Carga do pipeline no banco (D.5, D.7, D.8, D.9) | Substituída pelo seed de demonstração em 2026-10-06; endoflife e NVD ficam só como referência em `dataset/processed/` | `ROADMAP.md:216,222-226` |
| Transição de status da recomendação (proposta → aprovada → implementada) | O contrato não tem `PATCH` | `ROADMAP.md:198` |
| Alertas MÉDIO/BAIXO do FR-004 sem código CP | Sem código de regra | `ROADMAP.md:165` |

### 4.3 Limitações conhecidas

- **Baixa retroativa.** Uma baixa com data retroativa pode ficar anterior a um vínculo de licença que ela encerra (`ROADMAP.md:259`).
- **`total_rejeitado` da importação.** O campo conta erros, não linhas (`ROADMAP.md:244`).
- **Validação permissiva do Pydantic.** Aceita `0` como booleano (`ROADMAP.md:208`).
- **Pendência de alinhamento.** Divergência entre o `data_source` de licença no PRD e no código, e `FornecedorCreate` expondo `data_source` (`ROADMAP.md:248`).

---

## 5. Ajustes funcionais

### 5.1 Código

| Ajuste | Rastreabilidade | Registro |
|---|---|---|
| Unicidade da chave de licença do ativo: índice único parcial `ux_ativo_chave_licenca` (migração `d4a6c8e0f1b2`), recusa 409 `BR-039` com `RECUSADO` na auditoria e sem expor a chave (RI-08). `licenca.chave_licenca` fica sem unicidade, porque a renovação de subscrição pode repetir a chave | BR-039, AC-067; decisão da equipe de 2026-10-05 | `ROADMAP.md:67`; REGISTRO entrada 27 |
| Coluna opcional `data_source` na importação (`compras_gov` ou `importacao`; vazia grava `importacao`; outro valor é erro de linha) | FR-008, AC-071 | `ROADMAP.md:78`; REGISTRO entrada 30 |
| Importação sem derrubar o arquivo: texto acima do tamanho da coluna e `valor_compra` fora da precisão viram erro de linha, não 422 do arquivo inteiro | FR-008, AC-068, AC-069 | `ROADMAP.md:79`; REGISTRO entrada 29 |
| Corrida no número de série: conflito real no índice passou de 500 para 409 `BR-001`, auditado e contado | BR-001, AC-070 | `ROADMAP.md:80` |
| Importação em lote audita: uma linha `CRIAR`/`ativo` por aceito e uma `CRIAR`/`lote_importacao`, na mesma transação | BR-030, AC-057 | `ROADMAP.md:81`; falha 34 do REGISTRO |
| Lock `FOR NO KEY UPDATE` na transferência. Com `FOR UPDATE`, o `KEY SHARE` da FK de um insert externo nunca conflitava, e o `except` de BR-007 era código morto | BR-007, NFR-AUD-05 | `ROADMAP.md:110`; falha 07 do REGISTRO; teste `test_br007_conflito_real_no_indice_grava_recusa_na_auditoria` |
| Correções achadas pelos testes de contrato (schemathesis 4.10.2): id acima de 32 bits deixou de dar 500 e passou a 422; erros do framework passaram ao formato único `/erros/http-<status>`; o `openapi.yaml` passou a documentar 400, 401, 403, 404, 409 e 422 com `ErroResponse`. Sem 500 residual em 45 operações | NFR-MAN-01, ADR-009 | `ROADMAP.md:203-210`; falha 33 do REGISTRO |
| Depreciação arredonda só no resultado final (`valor × meses ÷ vida útil`) | FR-003, BR-017, AC-020 | `ROADMAP.md:100`; falha 03 do REGISTRO |
| Trilha de auditoria imutável (trigger no `audit_log`) | NFR-AUD-01 | REGISTRO entrada 16; falha 10 |
| Recusa de inicialização com `SECRET_KEY` padrão fora de `local` | NFR-SEG, `configuracao.md` §13.1 | `ROADMAP.md:161` |
| "Hoje" do domínio no fuso `America/Recife` | BR-003, FR-004 | `ROADMAP.md:242` |
| Swagger com HTTP Bearer, no lugar do fluxo OAuth2, que dava 422 no login | FR-015 | `ROADMAP.md:240` |

### 5.2 Orquestração

| Ajuste | Registro |
|---|---|
| PostgreSQL 16 acrescentado ao Compose, com health check e banco `itam_test` criado na primeira subida (`infra/postgres/init/01-banco-de-teste.sql`) | `docker-compose.yml`; `ROADMAP.md:50` |
| A API migra o banco ao subir (`python/entrypoint.sh`); `healthcheck` na API; o Prometheus espera a API saudável | `ROADMAP.md:160,174` |
| CI em `.github/workflows/ci.yml`: qualidade (ruff, mypy, bandit), suíte em PostgreSQL 16, cobertura ≥ 70% global e 100% em `utils/` + `services/`, e contagem de testes `test_ac` | `ROADMAP.md:52`; `ci.yml` |
| Grafana provisionado com 2 dashboards na pasta "Governança de TI" | `ROADMAP.md:154,158` |
| Seed básico (`scripts/seed.sh`) e seed de demonstração dos Gates 2, 3 e 4 (`scripts/seed_demo.sh`), pelos services e idempotente | `ROADMAP.md:227` |
| `scripts/smoke_test.sh` cobrindo API, banco, rotas, `/metrics`, alvo do Prometheus e os 2 dashboards | `ROADMAP.md:187` |

### 5.3 Documentação

| Ajuste | Registro |
|---|---|
| ADR-013: o PRD prevalece em regra de negócio, o SPEC em implementação | `docs/adr/0013-precedencia-prd-spec.md` |
| ADR-012: software é ativo (resolve QA-06) | `docs/adr/0012-software-como-ativo.md` |
| ADR-011 corrigida contra a API real do Compras.gov.br (endpoint `/modulo-pesquisa-preco/1_consultarMaterial`, identificador `CG-{idItemCompra}-001`) | `ROADMAP.md:216`; falhas 36 e 37 do REGISTRO |
| Arquivo do Gate 1 (`dataset/demo/inventario_demo.csv`: 100 linhas reais, 92 válidas e 8 inválidas de propósito). Estava versionado com 0 bytes | `ROADMAP.md:219`; falha 35 do REGISTRO |
| Sanitização de possível CPF em razão social nas fixtures (LGPD) | `ROADMAP.md:241` |
| NFR-MAN-05, P6, ADR-007 e RI-10 marcados como revisados: o SQLite só executa a aplicação, e os testes rodam em PostgreSQL 16 | `ROADMAP.md:258` |

---

## 6. Registro de atividades

O histórico do git tem um único autor de commit, que versionou o trabalho da equipe. Por isso, a coluna "Frente" indica a frente técnica do anexo à qual a atividade pertence, e não a autoria do commit. [A EQUIPE CONFIRMA: quem executou cada atividade.]

| Data | Atividade | Frente | Artefato | Evidência |
|---|---|---|---|---|
| 2026-09-02 | Recebimento da baseline do Projeto 3 e remoção das referências a Java | Infra/DevOps | Repositório inicial | `64e9e18`, `deabe82` |
| 2026-09-20 | Redação do PRD, do SPEC, da arquitetura, do modelo de dados, do backlog e dos datasets sintéticos com apoio de IA | Documentação | `docs/PRD.md`, `docs/SPEC.md` (depois divididos) | REGISTRO entradas 01 a 05 |
| 2026-09-22 | Troca do domínio de Observabilidade para ITAM | Documentação | PRD (1464 linhas), SPEC (1013), modelo de dados, backlog, datasets ITAM | `45f402e` |
| 2026-09-23 | Docker atualizado para a nova aplicação | Infra/DevOps | `docker-compose.yml` | commits de 2026-09-23 |
| 2026-09-27 | Fontes de dados reais e ADR-011; reorganização de diretórios; CI; Sprint 0 (Gate 0); Sprint 1 (modelos, JWT, RBAC, ativos, importação, auditoria) | Infra/DevOps, Backend, ETL | `docs/FONTES_DE_DADOS.md`, `ci.yml`, `python/app/` | REGISTRO entradas 06 a 12 |
| 2026-09-29 | ADR-012 (software como ativo) | Documentação | `docs/adr/0012-software-como-ativo.md` | REGISTRO entrada 13 |
| 2026-09-30 | Resolução de pendências do Sprint 2 (itens 0 a 15), ADR-013 e suíte inteira em PostgreSQL 16 | Backend, Documentação | ADR-013, `conftest.py` | REGISTRO entrada 14; `ROADMAP.md:98-109` |
| 2026-10-02 | Sprint 2 (histórico e depreciação); Sprint 3 (baixa e licenças); Sprint 4 (compliance, relatórios, indicadores, `/health`, `/metrics`, dashboard `itam-tecnico`); migração automática e healthcheck | Backend, Infra/DevOps | migrações, services, `infra/grafana/` | REGISTRO entradas 15 a 22; 80 commits na data |
| 2026-10-03 | Sprint 5 (riscos, scorecard, cenários, recomendação); testes de contrato; validação da `SECRET_KEY` | Backend, Infra/DevOps | `tests/contract/`, `scripts/start.sh` | REGISTRO entrada 23 |
| 2026-10-05 | BR-039 (chave única); coletor `compras_gov` (D.1); arquivo do Gate 1 (D.2); correções do importador (AC-068 a AC-071); seed de demonstração dos Gates 2 e 3; correções do Docker (Swagger Bearer, MEI, fuso) | Backend, ETL, Scripts | `collectors/compras_gov.py`, `dataset/demo/`, `app/seed_demo.py` | REGISTRO entradas 26 a 33 |
| 2026-10-06 | Sanitização de CPF; seed do Gate 4; métricas de negócio e dashboard `itam-gestao`; coletores `endoflife` (D.3) e `nvd` (D.4); normalização (D.6); testes no fuso de Recife | ETL, Backend, Infra/Grafana | `etl/normalizar.py`, `infra/grafana/dashboards/itam-gestao.json` | REGISTRO entradas 35 a 38; commit `d6583d8` |

---

## Anexo — Equipe e divisão de frentes

| Integrante | Frente |
|---|---|
| Edilson Pereira da Silva Filho | ETL e dados |
| Gabriel Leal de Andrade Pereira | Backend |
| João Victor Azevedo de Sena | Infra, PostgreSQL, DevOps, CI, Grafana e observabilidade |
| Paulo Gabriel Morais Santana da Silva | Backend e scripts |
| Vinícius Alencar Murta Costa | Documentação |
