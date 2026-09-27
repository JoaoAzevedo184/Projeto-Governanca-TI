# Guia — Contribuição

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Contribuição

**Branches:** `main` protegida; trabalho em `feat/`, `fix/` ou `docs/`.

**Commits:** padrão Conventional Commits, referenciando o requisito.

```
feat(ativos): implementa bloqueio de número de série duplicado (FR-001, BR-001)
fix(depreciacao): corrige arredondamento para half-up (BR-017)
test(licencas): cobre AC-021 — excedente de quantitativo
feat(collectors): adiciona coletor do Compras.gov por CATMAT (FR-001)
```

**Definition of Done:** testes do critério passando · migração aplicada e reversível · `openapi.yaml` regenerado · `ruff check` limpo · README atualizado se a forma de execução mudou · novos dados com `data_source` preenchido.

