# Modelo de Dados — Índices

Parte de [Modelo de Dados — ITAM](README.md).

## 5. Índices

| Tabela | Índice | Tipo | Motivo |
|---|---|---|---|
| `ativo` | `numero_serie` | único | BR-001 |
| `ativo` | `status` | btree | Filtro mais usado |
| `ativo` | `categoria_id`, `fornecedor_id` | btree | Filtros de relatório |
| `ativo` | `data_aquisicao` | btree | Faixas de período e idade |
| `ativo` | `lower(nome)` | btree | Busca textual |
| `historico_transferencia` | `(ativo_id) WHERE data_fim IS NULL` | **único parcial** | BR-007 |
| `historico_transferencia` | `(ativo_id, data_inicio DESC)` | btree | Linha do tempo |
| `historico_transferencia` | `responsavel_id` | btree | "O que está com fulano" |
| `baixa_ativo` | `ativo_id` | único | BR-024 |
| `baixa_ativo` | `data_baixa` | btree | Relatório por período |
| `licenca_vinculo` | `(licenca_id, ativo_id) WHERE ativo_vinculo` | único parcial | Evita duplicata |
| `licenca` | `data_expiracao` | btree | Varredura de vencimento |
| `audit_log` | `(entidade, entidade_id)`, `carimbo` | btree | Consulta de auditoria |

