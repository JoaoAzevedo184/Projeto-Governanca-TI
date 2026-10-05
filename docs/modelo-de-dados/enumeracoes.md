# Modelo de Dados — Enumerações

Parte de [Modelo de Dados — ITAM](README.md).

## 2. Enumerações

| Enum | Valores | Usado em |
|---|---|---|
| `tipo_ativo` | `HARDWARE`, `SOFTWARE` | `ativo.tipo`, `categoria.tipo_aplicavel` |
| `status_ativo` | `ATIVO`, `EM_MANUTENCAO`, `BAIXADO` | `ativo.status` |
| `motivo_baixa` | `OBSOLESCENCIA`, `DEFEITO`, `FURTO_ROUBO`, `FIM_VIDA_UTIL`, `OUTRO` | `baixa_ativo.motivo` |
| `destinacao_baixa` | `RECICLAGEM_CERTIFICADA`, `DOACAO`, `DEVOLUCAO_FORNECEDOR`, `VENDA`, `DESCARTE` | `baixa_ativo.destinacao` |
| `tipo_licenciamento` | `PERPETUA`, `SUBSCRICAO`, `OEM` | `licenca.tipo_licenciamento` |
| `perfil_usuario` | `ADMIN`, `OPERADOR`, `GESTOR`, `AUDITOR` | `usuario.perfil` |
| `categoria_risco` | `OPERACIONAL`, `FINANCEIRO`, `LEGAL`, `SEGURANCA`, `CONTINUIDADE` | `risco.categoria` |
| `resposta_risco` | `ACEITAR`, `MITIGAR`, `TRANSFERIR`, `EVITAR` | `risco.resposta` |
| `status_risco` | `ABERTO`, `EM_TRATAMENTO`, `ENCERRADO` | `risco.status` (valores definidos na Sprint 5: o PRD cita o campo sem os valores) |
| `classificacao_risco` | `BAIXO`, `MEDIO`, `ALTO`, `CRITICO` | derivada do `score`, não é coluna (`utils/risco.py`) |
| `nome_cenario` | `MANTER`, `RENOVAR`, `MIGRAR_ASSINATURA` | entrada de `/cenarios/comparar`, sem tabela |
| `status_recomendacao` | `PROPOSTA`, `APROVADA`, `REJEITADA`, `IMPLEMENTADA` | `recomendacao.status` |
| `tipo_evidencia` | `INDICADOR`, `RISCO`, `ATIVO`, `LICENCA`, `SCORECARD`, `CENARIO`, `PREMISSA` | `evidencia.tipo`. `RISCO`, `ATIVO`, `LICENCA` e `SCORECARD` (id do fornecedor) apontam para um registro (`referencia_id`); `INDICADOR`, `CENARIO` e `PREMISSA` não têm registro e levam só `descricao` |
| `data_source` | `compras_gov`, `endoflife`, `nvd` (fontes reais, ADR-011); `sintetico` (ETL); `importacao` (planilha via `POST /importacoes`; a planilha pode declarar `compras_gov` na coluna `data_source`); `manual` (cadastro direto pela API) | Coluna presente em toda tabela com origem rastreável — ver [`docs/FONTES_DE_DADOS.md`](../FONTES_DE_DADOS.md). Ainda sem `CHECK` no schema |

Todos implementados como `VARCHAR` com `CHECK`, nunca como `ENUM` nativo do PostgreSQL (ADR-007): enums nativos exigem migração dedicada para cada valor novo e não existem no SQLite.

