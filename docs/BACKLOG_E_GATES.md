# Backlog e Gates — ITAM

Planejamento de execução do MVP de Gestão de Ativos de TI. Os identificadores `FR-`, `BR-`, `AC-` e `NFR-` referenciam o [`PRD.md`](PRD.md); os detalhes técnicos estão no [`SPEC.md`](SPEC.md).

---

## 1. Gates

Cada gate é um ponto de verificação com entrega obrigatória. Não se avança sem liberar o anterior.

### Gate 0 — Enquadramento

**Entrega:** cenário do problema, escopo e não escopo, personas, especificação inicial (`PRD-ITAM.md`), critérios de avaliação e registro de uso de IA.

**Liberação:** o escopo está delimitado por escrito e a equipe consegue responder o que o sistema **não** fará.

| Artefato | Estado |
|---|---|
| `docs/PRD-ITAM.md` | Completo |
| `docs/ARQUITETURA.md` | Completo |
| `docs/MODELO_DE_DADOS.md` | Completo |
| `docs/REGISTRO_USO_IA.md` | Aberto, atualizado continuamente |
| Repositório com estrutura de pastas e CI | A fazer |

---

### Gate 1 — Inventário operacional

**Entrega:** dataset de ativos importável, API de cadastro funcionando, casos públicos de importação, testes de unicidade e validação.

**Liberação:** um arquivo de 100 linhas é importado, gera 92 ativos e um relatório de 8 erros linha a linha.

| Verificação | Critério |
|---|---|
| Cadastro com todos os campos obrigatórios | AC-001 |
| Recusa de número de série duplicado | AC-002, AC-046 |
| Recusa de cabeçalho divergente antes de processar | AC-045 |
| Relatório de erros com linha, campo e motivo | AC-044 |
| Autenticação e perfis operando | AC-055, AC-056 |

**Dados liberados neste gate:** `datasets/inventario.csv`, `datasets/categorias.csv`, `datasets/fornecedores.csv`.

---

### Gate 2 — Responsabilidade e valor

**Entrega:** histórico de transferências imutável, cálculo de depreciação, relatório de valor residual conciliável.

**Liberação:** a equipe demonstra a linha do tempo de um ativo com três transferências, sem sobreposição de períodos, e o valor residual bate com o cálculo manual.

| Verificação | Critério |
|---|---|
| Transferência encerra vínculo anterior na mesma transação | AC-010 |
| Ativo baixado não recebe responsável | AC-011 |
| Vínculo encerrado não pode ser editado nem excluído | AC-013 |
| Depreciação de R$ 6.000 / 60 meses / 12 meses = R$ 4.800 residual | AC-015 |
| Valor residual nunca negativo | AC-017 |

**Dados liberados neste gate:** `datasets/responsaveis.csv`, `datasets/setores.csv`, `datasets/transferencias.csv`.

---

### Gate 3 — Conformidade e evento surpresa

**Entrega:** controle de licenças com bloqueio de excedente, baixas com destinação, painel de compliance.

**Evento surpresa:** o professor injeta no ambiente um cenário de desconformidade — por exemplo, um lote de vínculos que leva uma licença de 50 para 53 em uso, ou uma licença vencida há 40 dias. A equipe tem prazo limitado para detectar, explicar e propor correção, sustentada em evidência.

**Liberação:** o sistema **bloqueou** a operação irregular, **registrou** a tentativa na auditoria e a equipe **explicou** a regra violada citando o identificador.

| Verificação | Critério |
|---|---|
| Bloqueio da vinculação acima do contratado | AC-021 |
| Licença vencida sinalizada como Crítico | AC-023 |
| Ativo sem responsável sinalizado | AC-039 |
| Baixa congela o valor residual na data | AC-019 |
| Baixa sem destinação recusada | AC-033 |
| Tentativa bloqueada consta na trilha de auditoria | NFR-AUD-05 |

**Dados liberados neste gate:** `datasets/licencas.csv`, `datasets/licenca_vinculos.csv`, `datasets/baixas.csv`.

---

### Gate 4 — Decisão e defesa

**Entrega:** indicadores, dashboard, comparação de cenários, scorecard, registro de riscos, recomendação rastreável, deploy funcionando e apresentação de 5 minutos.

**Liberação:** a recomendação apresentada na defesa é aberta no sistema e cada evidência que a sustenta é exibida ao vivo.

| Verificação | Critério |
|---|---|
| Indicador retorna fórmula e amostra | AC-047 |
| Scorecard recusa pesos que não somam 100% | AC-048 |
| Risco 4 × 5 classificado como Crítico | AC-050 |
| Recomendação sem evidência é recusada | AC-051 |
| Cenários ordenados sem escolha automática | AC-052 |
| `/health` e `/metrics` respondendo | AC-053, AC-054 |
| Grafana exibindo o dashboard provisionado | FR-014 |

**Dados liberados neste gate:** `datasets/riscos.csv`, `datasets/custos_cenarios.csv`, `datasets/dashboard_referencia.csv`.

---

## 2. Sprints

| Sprint | Tema | Gate |
|---|---|---|
| Sprint 0 | Preparação e discovery | Gate 0 |
| Sprint 1 | Ingestão e inventário | Gate 1 |
| Sprint 2 | Responsabilidade e depreciação | Gate 2 |
| Sprint 3 | Licenças, baixas e compliance | Gate 3 |
| Sprint 4 | Indicadores, relatórios e observabilidade | Gate 4 |
| Sprint 5 | Decisão, qualidade e defesa | Gate 4 |

---

## 3. Backlog por sprint

### Sprint 0 — Preparação

| # | Item | FR/NFR | Saída |
|---|---|---|---|
| 0.1 | Criar repositório com a estrutura de pastas do SPEC | — | Árvore de diretórios |
| 0.2 | Configurar `docker-compose.yml` com API, PostgreSQL, Prometheus e Grafana | NFR-MAN-04 | Ambiente sobe com um comando |
| 0.3 | Inicializar Alembic e a migração base | NFR-MAN-06 | `alembic upgrade head` funcional |
| 0.4 | Pipeline de CI com ruff, mypy, bandit e pytest | NFR-SEG-05 | Build verde |
| 0.5 | Escrever `openapi.yaml` inicial a partir do SPEC | NFR-MAN-01 | Contrato versionado |
| 0.6 | Registrar ADR-001 a ADR-003 | — | `docs/adr/` |
| 0.7 | Definir papéis da equipe e política de uso de IA | — | `README.md`, `REGISTRO_USO_IA.md` |

### Sprint 1 — Ingestão e inventário

| # | Item | FR/NFR | Critérios |
|---|---|---|---|
| 1.1 | Modelos `categoria`, `fornecedor`, `setor`, `responsavel`, `usuario` | FR-001 | — |
| 1.2 | Modelo `ativo` com `ck_ativo_identificador` e índices | FR-001 | AC-003, AC-004 |
| 1.3 | Autenticação JWT e hash BCrypt | FR-015 | AC-056 |
| 1.4 | Dependência `require_perfil` e matriz RBAC | FR-015 | AC-055 |
| 1.5 | `POST/GET/PATCH /ativos` com paginação e filtros | FR-001 | AC-001, AC-008 |
| 1.6 | Unicidade de número de série | BR-001 | AC-002 |
| 1.7 | Validações de data e valor | BR-003, BR-004 | AC-005, AC-006 |
| 1.8 | Herança de vida útil da categoria | BR-006 | AC-007 |
| 1.9 | Pipeline de importação CSV/XLSX | FR-008 | AC-044 a AC-046 |
| 1.10 | `LoteImportacao` e `ErroImportacao` | FR-008 | AC-044 |
| 1.11 | Trilha de auditoria em toda escrita | NFR-AUD-02 | AC-057 |
| 1.12 | Handler global de erros com campo `regra` | NFR-SEG-06 | — |

### Sprint 2 — Responsabilidade e depreciação

| # | Item | FR/NFR | Critérios |
|---|---|---|---|
| 2.1 | Modelo `historico_transferencia` com índice único parcial | BR-007 | AC-012 |
| 2.2 | Trigger de imutabilidade e exceção controlada de `data_fim` | NFR-AUD-01 | AC-013 |
| 2.3 | `POST /ativos/{id}/responsavel` (atribuição e transferência) | FR-002 | AC-009, AC-010 |
| 2.4 | Bloqueio de atribuição em ativo baixado | BR-009 | AC-011 |
| 2.5 | Validação de data de início ≥ aquisição | BR-010 | AC-014 |
| 2.6 | `GET /ativos/{id}/historico` | FR-002 | AC-012 |
| 2.7 | `utils/depreciacao.py` como função pura com `Decimal` | FR-003 | AC-015 a AC-020 |
| 2.8 | `GET /ativos/{id}/depreciacao` com fórmula exposta | FR-003 | AC-015 |
| 2.9 | Casos de borda: zero meses, vida esgotada, vida de 1 mês | BR-014 | AC-016, AC-017 |

### Sprint 3 — Licenças, baixas e compliance

| # | Item | FR/NFR | Critérios |
|---|---|---|---|
| 3.1 | Modelos `licenca` e `licenca_vinculo` | FR-004 | — |
| 3.2 | `quantidade_em_uso` derivada por COUNT | BR-021 | AC-026 |
| 3.3 | Bloqueio de vinculação acima do contratado | BR-018 | AC-021 |
| 3.4 | Bloqueio de vinculação em licença vencida | BR-020 | AC-025 |
| 3.5 | Cálculo de `dias_para_expiracao` e status de conformidade | FR-004 | AC-022, AC-023 |
| 3.6 | Modelo `baixa_ativo` com UNIQUE em `ativo_id` | BR-024 | AC-030 |
| 3.7 | `POST /ativos/{id}/baixa` em transação única | FR-005 | AC-027 |
| 3.8 | Congelamento do valor residual na data da baixa | BR-015 | AC-019 |
| 3.9 | Validações de motivo, justificativa, data e destinação | BR-022, BR-023, BR-026 | AC-028, AC-029, AC-033 |
| 3.10 | `compliance_service` com as nove regras CP-01 a CP-09 | FR-007 | AC-039 a AC-043 |
| 3.11 | Registro de tentativas bloqueadas na auditoria | NFR-AUD-05 | — |

### Sprint 4 — Indicadores, relatórios e observabilidade

| # | Item | FR/NFR | Critérios |
|---|---|---|---|
| 4.1 | `GET /relatorios/inventario` com filtros combináveis | FR-006 | AC-034, AC-035 |
| 4.2 | Exportação CSV/XLSX com cabeçalho de procedência | FR-006 | AC-036, AC-037 |
| 4.3 | Filtro de fim de vida útil (≥ 80%) | FR-006 | AC-038 |
| 4.4 | Relatórios de depreciação, conformidade, baixas e histórico | FR-006 | — |
| 4.5 | `GET /indicadores` com fórmula e amostra | FR-009 | AC-047 |
| 4.6 | `GET /compliance/alertas` agrupado por severidade | FR-007 | AC-040 a AC-042 |
| 4.7 | `/health` com estado de aplicação e banco | NFR-DIS-03 | AC-053 |
| 4.8 | `/metrics` com as seis métricas do SPEC | NFR-OBS-01 | AC-054 |
| 4.9 | Provisionamento do datasource e do dashboard Grafana | FR-014 | — |
| 4.10 | Log estruturado em JSON | NFR-OBS-03 | — |

### Sprint 5 — Decisão, qualidade e defesa

| # | Item | FR/NFR | Critérios |
|---|---|---|---|
| 5.1 | `POST /cenarios/comparar` sem seleção automática | BR-028 | AC-052 |
| 5.2 | `POST /fornecedores/scorecard` com validação de pesos | BR-029 | AC-048, AC-049 |
| 5.3 | CRUD de riscos com score gerado | FR-012 | AC-050 |
| 5.4 | `POST /recomendacoes` exigindo evidência | BR-027 | AC-051 |
| 5.5 | Testes de contrato contra `openapi.yaml` | NFR-MAN-01 | — |
| 5.6 | Cobertura ≥ 70% global, 100% em `utils/` e `services/` | NFR-MAN-03 | — |
| 5.7 | `scripts/smoke_test.sh` cobrindo os seis pontos | — | — |
| 5.8 | Documentação final e checklist de entrega | — | — |
| 5.9 | Roteiro de defesa de 5 minutos | — | — |

---

## 4. Definition of Done

Vale para todo item de backlog:

- [ ] Código na branch principal, revisado por outro integrante
- [ ] Migração aplicada e reversível (`alembic downgrade` testado)
- [ ] Testes dos critérios de aceite do item passando, nomeados `test_ac###_...`
- [ ] `openapi.yaml` regenerado e versionado, se a API mudou
- [ ] `ruff check` e `mypy` limpos
- [ ] Regra de negócio citada no código e na mensagem de erro
- [ ] `docker compose up` sobe o ambiente sem intervenção manual
- [ ] README atualizado, se a forma de execução mudou

---

## 5. Roteiro de defesa (5 minutos)

| Tempo | Conteúdo |
|---|---|
| 0:00–0:40 | O problema: inventário em planilhas, licenças sem controle, valor patrimonial congelado |
| 0:40–1:20 | Importação de um arquivo real, com o relatório de erros gerado ao vivo |
| 1:20–2:10 | Transferência de responsável e a linha do tempo imutável |
| 2:10–3:00 | Tentativa de vincular a 51ª instalação de uma licença de 50 — bloqueio e registro |
| 3:00–3:50 | Painel de compliance e indicadores, com a fórmula de um KPI exibida |
| 3:50–4:30 | Uma recomendação aberta, mostrando cada evidência que a sustenta |
| 4:30–5:00 | Aderência a COBIT BAI09, ITIL e ISO/IEC 19770 |

**Regra da defesa:** qualquer integrante deve conseguir explicar qualquer trecho. A distribuição de temas na apresentação não é distribuição de conhecimento.