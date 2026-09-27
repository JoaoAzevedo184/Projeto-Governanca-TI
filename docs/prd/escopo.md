# PRD — Escopo do MVP

Parte de [PRD — ITAM](README.md).

## 7. Escopo do MVP

### 7.1 Incluído no MVP

| ID | Item | Requisito relacionado |
|---|---|---|
| IN-01 | Cadastro, edição e consulta de ativos de hardware e software | FR-001 |
| IN-02 | Cadastro de categorias com vida útil configurável | FR-001, FR-003 |
| IN-03 | Cadastro de fornecedores | FR-001 |
| IN-04 | Cadastro de responsáveis (usuários e setores) | FR-002 |
| IN-05 | Atribuição e transferência de responsável com histórico | FR-002 |
| IN-06 | Cálculo automático de depreciação linear e valor residual | FR-003 |
| IN-07 | Cadastro de licenças com quantitativo contratado e em uso | FR-004 |
| IN-08 | Alertas de excedente e de expiração de licença | FR-004, FR-007 |
| IN-09 | Registro de baixa com motivo, data e destinação | FR-005 |
| IN-10 | Relatório de inventário com filtros combináveis | FR-006 |
| IN-11 | Painel de alertas de compliance | FR-007 |
| IN-12 | Importação de inventário via CSV/XLSX | FR-008 |
| IN-13 | Indicadores de ITAM e dashboard | FR-009, FR-014 |
| IN-14 | Autenticação JWT e perfis de acesso (RBAC) | NFR-SEG-01, NFR-SEG-02 |
| IN-15 | Trilha de auditoria imutável | NFR-AUD-01 |
| IN-16 | API REST documentada via OpenAPI | NFR-MAN-02 |
| IN-17 | Health check e métricas no padrão Prometheus | NFR-OBS-01, NFR-OBS-02 |

### 7.2 Fora do Escopo do MVP

| ID | Item excluído | Justificativa |
|---|---|---|
| OUT-01 | Integração com Active Directory / LDAP | Dependência de infraestrutura externa; usuários são cadastrados localmente no MVP |
| OUT-02 | Descoberta automática de inventário via agente | Exige desenvolvimento de cliente instalável, fora do escopo de um MVP de governança |
| OUT-03 | Integração com Microsoft SCCM / Intune | Dependência de licenciamento e ambiente corporativo indisponível |
| OUT-04 | Gestão financeira completa (contas a pagar, centro de custo, rateio) | Domínio de ERP; o MVP entrega apenas depreciação e valor residual |
| OUT-05 | Módulo de compras, cotações e contratos | Processo upstream; o MVP parte do ativo já adquirido |
| OUT-06 | Service Desk / abertura de chamados | Coberto pelo Projeto 1 da baseline da disciplina |
| OUT-07 | Leitura de QR Code / código de barras | Previsto para a V2 |
| OUT-08 | Upload de nota fiscal e anexos | Previsto para a V2 |
| OUT-09 | Gestão de garantia e contratos de manutenção | Previsto para a V2 |
| OUT-10 | Múltiplas moedas e múltiplas filiais | Assume-se moeda única (BRL) e organização única |
| OUT-11 | Métodos de depreciação além do linear | O linear atende à IN RFB 1.700; demais métodos na V2 |
| OUT-12 | Aplicativo móvel nativo | A interface web responsiva atende à Persona 2 |
| OUT-13 | Assinatura digital de termo de responsabilidade | Previsto para a V2 |

