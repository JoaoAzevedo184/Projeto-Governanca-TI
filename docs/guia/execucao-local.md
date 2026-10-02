# Guia — Execução Local sem Docker

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Execução local sem Docker

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

cp .env.example .env               # DATABASE_URL já aponta para SQLite

pip install -r python/requirements.txt
./scripts/seed.sh                  # migra o banco e carrega usuários de demonstração e categorias

cd python
uvicorn app.main:app --reload --port 8000
```

**Carga inicial.** `./scripts/seed.sh` roda `alembic upgrade head` e depois `python -m app.seed` (em `python/app/seed.py`), com o venv ativo. Ele cria os quatro usuários de demonstração (`admin`, `operador`, `gestor`, `auditor`, um por perfil) e as 11 categorias de [`dados-semente.md`](../modelo-de-dados/dados-semente.md). As senhas vêm das variáveis `SEED_*_PASSWORD` do `.env` (o `.env.example` traz valores didáticos); o script lê o `.env` da raiz, sem sobrepor variáveis já exportadas no shell. É idempotente e recusa rodar com `ENVIRONMENT=producao`. **Não carrega** os dados do pipeline (`dataset/processed/` e `dataset/synthetic/`): isso é a pendência D.9 do [`ROADMAP.md`](../ROADMAP.md). Sem eles, o banco local começa só com usuários e categorias; os ativos entram pela API ou pela importação de CSV (ver [`importacao.md`](importacao.md)).

O perfil local usa **SQLite**, sem necessidade de banco externo. O perfil Docker usa **PostgreSQL**. A seleção é feita pela variável `DATABASE_URL`.

*Revisado (item 13 de [`RESOLUCAO_PENDENCIAS_SPRINT2.md`](../RESOLUCAO_PENDENCIAS_SPRINT2.md)):* o SQLite serve só para executar a aplicação. Os testes rodam sempre contra PostgreSQL 16 (ver [`testes.md`](testes.md)). No SQLite não existe o trigger de imutabilidade do histórico, o lock de linha da transferência nem a verificação de chave estrangeira (`PRAGMA foreign_keys` fica desligado): use o perfil Docker para verificar a imutabilidade (BR-011, AC-013) e a concorrência da transferência (BR-007).

