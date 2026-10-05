# PRD — Anexos (Aderência a Frameworks, Rastreabilidade, Glossário)

Parte de [PRD — ITAM](README.md).

## Anexo A — Matriz de Aderência a Frameworks de Governança

| Framework | Referência específica | Requisitos que a implementam |
|---|---|---|
| **ISO/IEC 19770-1** | Sistema de gestão de ativos de TI: identificação, propriedade, ciclo de vida | FR-001, FR-002, FR-005, FR-006 |
| **ISO/IEC 19770-3** | Direitos de uso de software e entitlement | FR-004, FR-007 |
| **COBIT 2019 — BAI09** | Gerenciar Ativos: contabilizar, otimizar e proteger ao longo do ciclo de vida | FR-001, FR-003, FR-005, FR-009 |
| **COBIT 2019 — BAI10** | Gerenciar Configuração: registro confiável dos itens e seus atributos | FR-001, FR-008 |
| **COBIT 2019 — APO10** | Gerenciar Fornecedores: avaliação e monitoramento de desempenho | FR-011 |
| **COBIT 2019 — APO12** | Gerenciar Riscos: identificação, avaliação e resposta | FR-012, FR-007 |
| **COBIT 2019 — APO06** | Gerenciar Orçamento e Custos | FR-003, FR-010 |
| **ITIL 4** | Prática de Gestão de Ativos de TI | FR-001, FR-002, FR-005 |
| **ITIL 4** | Prática de Gestão de Configuração de Serviço | FR-001, FR-006 |
| **ISO/IEC 38500** | Princípio da Responsabilidade | FR-002, FR-015 |
| **ISO/IEC 38500** | Princípio da Aquisição | FR-010, FR-011 |
| **ISO/IEC 38500** | Princípio da Conformidade | FR-004, FR-007 |
| **Val IT** | Gestão do valor do investimento em TI | FR-003, FR-009, FR-010 |
| **Risk IT** | Risco de negócio associado ao uso de TI | FR-004, FR-007, FR-012 |
| **BSC — perspectiva financeira** | Indicadores de valor patrimonial e custo | KPI-05, FR-009, FR-010 |
| **BSC — perspectiva de processos** | Indicadores de cobertura e conformidade | KPI-01, KPI-02, KPI-03 |
| **TI Verde** | Descarte responsável de resíduos eletroeletrônicos | FR-005 (campo `destinacao`), relatório de baixas por destinação |
| **CMMI / MPS.BR** | Rastreabilidade de requisitos e gestão de configuração | Anexo B, NFR-MAN-01, NFR-MAN-06 |
| **IN RFB nº 1.700/2017** | Taxas de depreciação de bens do ativo imobilizado | FR-003, tabela de vida útil por categoria |

---

## Anexo B — Matriz de Rastreabilidade

| Requisito | Histórias | Regras de negócio | Critérios de aceite | Indicador associado |
|---|---|---|---|---|
| FR-001 | US-001 a US-006 | BR-001 a BR-006, BR-039 | AC-001 a AC-008, AC-067, AC-070 | KPI-01 |
| FR-002 | US-007 a US-011 | BR-007 a BR-012, BR-038 | AC-009 a AC-014, AC-065 | KPI-02 |
| FR-003 | US-012 a US-016 | BR-013 a BR-017 | AC-015 a AC-020 | KPI-05 |
| FR-004 | US-017 a US-021 | BR-018 a BR-021, BR-032 a BR-035, BR-037 | AC-021 a AC-026, AC-059 a AC-062, AC-064, AC-066 | KPI-03 |
| FR-005 | US-022 a US-025 | BR-022 a BR-026, BR-031, BR-036 | AC-027 a AC-033, AC-058, AC-063 | KPI-08 |
| FR-006 | US-026, US-027 | BR-014 | AC-034 a AC-038 | — |
| FR-007 | US-028 a US-030 | BR-007, BR-018, BR-026 | AC-039 a AC-043 | KPI-02, KPI-03 |
| FR-008 | US-031, US-032 | BR-001, BR-002, BR-003 | AC-044 a AC-046, AC-068, AC-069, AC-071 | KPI-01 |
| FR-009 | US-030 | — | AC-047 | KPI-01 a KPI-08 |
| FR-010 | US-033 | BR-028 | AC-052 | — |
| FR-011 | US-034 | BR-029 | AC-048, AC-049 | — |
| FR-012 | US-035 | — | AC-050 | — |
| FR-013 | US-036 | BR-027 | AC-051 | — |
| FR-014 | US-037 | — | AC-053, AC-054 | KPI-04 |
| FR-015 | US-038 a US-040 | BR-030 | AC-055 a AC-057 | — |

> FR-010 a FR-013 estão implementados (Sprint 5): AC-048 e AC-049 (`test_scorecard_api.py`), AC-050 (`test_riscos.py`), AC-051 (`test_recomendacoes.py`) e AC-052 (`test_cenarios_api.py`), com BR-027, BR-028 e BR-029.

> **Fora do MVP:** KPI-01, KPI-04 e KPI-05 aparecem na matriz como indicador associado, mas o sistema não os calcula (ver `visao-geral.md` §4.3).

---

## Anexo C — Glossário

| Termo | Definição |
|---|---|
| **Ativo de TI** | Qualquer item de hardware ou software de valor econômico sob gestão da área de tecnologia |
| **Baixa** | Evento terminal que retira o ativo do inventário operacional, preservando seu histórico |
| **CAPEX** | Despesa de capital: investimento em aquisição de bens |
| **Amortização** | Equivalente contábil da depreciação para bem intangível (CPC 04). No sistema, para ativos do tipo `SOFTWARE`, o valor chamado de "depreciação" na API e no código representa contabilmente a amortização; o cálculo é o mesmo (linear, sem residual) |
| **Depreciação linear** | Método que distribui uniformemente o valor do bem ao longo de sua vida útil |
| **Entitlement** | Direito de uso de software concedido por uma licença |
| **Licença perpétua** | Direito de uso por prazo indeterminado, pago uma vez. É ativo (`tipo = SOFTWARE`) e deprecia pela vida útil da categoria |
| **ITAM** | *IT Asset Management* — gestão de ativos de tecnologia da informação |
| **OEM** | Software pré-instalado no equipamento, com custo embutido no hardware. Não é ativo separado |
| **OPEX** | Despesa operacional: custo recorrente de manutenção e operação |
| **RBAC** | *Role-Based Access Control* — controle de acesso por perfil |
| **Subscrição** | Direito de uso por período determinado, com pagamento recorrente. É despesa, registrada só como licença com vigência; não é ativo |
| **TCO** | *Total Cost of Ownership* — custo total de propriedade ao longo do ciclo de vida |
| **Valor residual** | Valor contábil remanescente após a depreciação acumulada |
| **Vida útil** | Período estimado de uso econômico do bem, em meses |
