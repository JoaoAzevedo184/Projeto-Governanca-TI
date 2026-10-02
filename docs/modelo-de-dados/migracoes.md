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

**Estado atual da garantia de imutabilidade no banco (PostgreSQL), conferido em 2026-10-02:**

| Tabela | Trigger | Migração | Teste |
|---|---|---|---|
| `historico_transferencia` | `tg_historico_imutavel` (`permitir_apenas_encerramento`) | `c8365ce7e5e4` (Sprint 2) | `tests/integration/test_historico_postgres.py` (AC-013) |
| `audit_log` | `tg_audit_imutavel` (`bloquear_mutacao`) | `25b1f6d20128` | `tests/integration/test_audit_log_postgres.py` (NFR-AUD-01) |
| `baixa_ativo` | `tg_baixa_imutavel` (`bloquear_mutacao`) | `ee62f9bcb421` (Sprint 3) | `tests/integration/test_baixa_postgres.py` (NFR-AUD-01) |

A função `bloquear_mutacao()` é criada por `25b1f6d20128` e reaplicada com `CREATE OR REPLACE` por `ee62f9bcb421`. O `downgrade` de `ee62f9bcb421` remove só o trigger de `baixa_ativo` (e a tabela) e **não** remove a função, porque `audit_log` continua dependendo dela.

Os nomes `0001_base` a `0008_auditoria` acima são o plano original; as revisões reais do Alembic têm identificadores gerados (`alembic/versions/`). Revisões da Sprint 3: `ee62f9bcb421` (`baixa_ativo`, `UNIQUE (ativo_id)`, CHECKs de enum, de resíduo e de justificativa, e o trigger) e `f5f9acc0de7b` (`licenca` com `ck_licenca_tipo`, `ck_licenca_vigencia` e demais CHECKs, e `licenca_vinculo` com o índice parcial `ux_licenca_ativo`). Em SQLite o índice parcial é criado e o trigger não (`_postgres()`). No SQLite nenhum desses triggers é criado (`_postgres()`). O `TRUNCATE` que o `conftest.py` usa entre os testes não aciona trigger de linha; um `TRUNCATE` direto em `audit_log` não é bloqueado.

Toda migração precisa de `downgrade` funcional e testado. Triggers e funções são criados e removidos na própria migração, nunca por script externo — do contrário o ambiente do professor diverge do da equipe no primeiro `alembic upgrade head`.

**Compatibilidade com SQLite:** triggers em PL/pgSQL não existem no SQLite. No perfil local (SQLite), a migração `c8365ce7e5e4` não cria o trigger (`_postgres()`). Nenhum serviço bloqueia UPDATE ou DELETE no histórico: a imutabilidade depende só de a API não expor rota que altere ou apague vínculo (o serviço apenas encerra o vínculo aberto). Escrita direta no banco SQLite é aceita, inclusive com chave estrangeira inválida (`PRAGMA foreign_keys` fica desligado). A suíte de testes inteira roda contra PostgreSQL 16, local e no CI (item 13 de [`RESOLUCAO_PENDENCIAS_SPRINT2.md`](../RESOLUCAO_PENDENCIAS_SPRINT2.md)), então AC-013 é sempre verificado com o trigger real.