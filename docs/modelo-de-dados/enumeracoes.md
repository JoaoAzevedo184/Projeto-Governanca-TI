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
| `status_recomendacao` | `PROPOSTA`, `APROVADA`, `REJEITADA`, `IMPLEMENTADA` | `recomendacao.status` |
| `tipo_evidencia` | `INDICADOR`, `RISCO`, `ATIVO`, `LICENCA`, `SCORECARD`, `CENARIO`, `PREMISSA` | `evidencia.tipo` |
| `data_source` | `compras_gov`, `endoflife`, `nvd`, `sintetico`, `importacao` | Coluna presente em toda tabela populada a partir de fonte externa ou de geração sintética — ver [`docs/FONTES_DE_DADOS.md`](../FONTES_DE_DADOS.md) |

Todos implementados como `VARCHAR` com `CHECK`, nunca como `ENUM` nativo do PostgreSQL (ADR-007): enums nativos exigem migração dedicada para cada valor novo e não existem no SQLite.

