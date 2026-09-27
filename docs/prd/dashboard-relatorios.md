# PRD — Dashboard e Relatórios

Parte de [PRD — ITAM](README.md).

## 16. Dashboard e Relatórios

### 16.1 Painel inicial — cartões de indicadores

| Cartão | Conteúdo | Origem |
|---|---|---|
| Total de ativos | Contagem geral, com desdobramento por status | FR-009 |
| Hardware x Software | Proporção por tipo | FR-009 |
| Valor patrimonial bruto | Soma dos valores de compra dos ativos não baixados | FR-009 |
| Valor depreciado | Depreciação acumulada do parque, em valor e percentual | FR-003, FR-009 |
| Valor residual | Soma dos valores residuais | FR-003, FR-009 |
| Licenças vencendo | Contagem de licenças com expiração em ≤ 30 dias | FR-004 |
| Ativos sem responsável | Contagem de ativos ativos sem vínculo aberto | FR-002 |
| Ativos em manutenção | Contagem com status `EM_MANUTENCAO` | FR-001 |
| Não conformidades | Total de alertas abertos, por severidade | FR-007 |
| Idade média do parque | Em meses | FR-009 |

### 16.2 Gráficos

| Gráfico | Tipo | Eixos |
|---|---|---|
| Distribuição por categoria | Barras horizontais | Categoria × contagem |
| Evolução do valor residual | Linha | Mês × valor residual total |
| Ativos por status | Rosca | Proporção entre ativo, manutenção e baixado |
| Conformidade de licenças | Barras empilhadas | Licença × contratado e em uso |
| Baixas por motivo | Barras | Motivo × contagem no período |
| Ativos por faixa de idade | Histograma | Faixa etária × contagem |

### 16.3 Relatórios disponíveis

| Relatório | Público-alvo | Formatos |
|---|---|---|
| Inventário completo com filtros | Administrador, Patrimônio | Tela, CSV, XLSX |
| Depreciação e valor residual por ativo | Patrimônio, Contabilidade | CSV, XLSX |
| Conformidade de licenças | Auditoria, Compliance | Tela, CSV |
| Histórico de responsáveis por ativo | Auditoria | Tela, CSV |
| Termo de responsabilidade por colaborador | Administrador, RH | Tela, CSV |
| Baixas por período e destinação | Patrimônio, Sustentabilidade | CSV |
| Não conformidades abertas | Auditoria | Tela, CSV |
| Ativos próximos do fim da vida útil | Administrador, Direção | Tela, CSV |
| Erros de importação por lote | Administrador | CSV |

### 16.4 Dashboard técnico (Grafana)

Provisionado automaticamente na pasta **Governança de TI**, com fonte de dados Prometheus:

- disponibilidade das APIs Python e Java;
- volume de requisições por minuto;
- distribuição de códigos de retorno;
- latência (percentis 50, 95 e 99);
- estado da conexão com o banco de dados.

