# Modelo de Dados — Migrações

Parte de [Modelo de Dados — ITAM](README.md).

## 9. Migrações

| Migração | Conteúdo |
|---|---|
| `0001_base` | `categoria`, `fornecedor`, `setor`, `responsavel`, `usuario` |
| `0002_ativo` | `ativo` com constraints e índices |
| `0003_historico` | `historico_transferencia`, índice único parcial, trigger de encerramento |
| `0004_baixa` | `baixa_ativo`, `UNIQUE (ativo_id)`, trigger de imutabilidade |
| `0005_licenca` | `licenca`, `licenca_vinculo`, índice parcial |
| `0006_importacao` | `lote_importacao`, `erro_importacao`, FK em `ativo` |
| `0007_governanca` | `risco`, `recomendacao`, `evidencia`, `fornecedor_avaliacao` |
| `0008_auditoria` | `audit_log`, trigger de imutabilidade, índices |
| `0009_data_source` | Coluna `data_source` em `ativo`, `fornecedor`, `responsavel`, `historico_transferencia`, `baixa_ativo`, `licenca`, `licenca_vinculo` |
| `0010_software_externo` | `produto_software`, `vulnerabilidade`, `ativo_software` |

Toda migração precisa de `downgrade` funcional e testado. Triggers e funções são criados e removidos na própria migração, nunca por script externo — do contrário o ambiente do professor diverge do da equipe no primeiro `alembic upgrade head`.

**Compatibilidade com SQLite:** triggers em PL/pgSQL não existem no SQLite. No perfil local, a imutabilidade cai para a camada de serviço. A suíte de testes inteira roda contra PostgreSQL 16, local e no CI (item 13 de [`RESOLUCAO_PENDENCIAS_SPRINT2.md`](../RESOLUCAO_PENDENCIAS_SPRINT2.md)), então AC-013 é sempre verificado com o trigger real.