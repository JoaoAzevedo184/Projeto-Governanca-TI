# Guia — Execução Local sem Docker

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Execução local sem Docker

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

cp .env.example .env               # DATABASE_URL já aponta para SQLite; ENVIRONMENT=local aceita a SECRET_KEY de exemplo

pip install -r python/requirements.txt
./scripts/seed.sh                  # migra o banco e carrega usuários de demonstração e categorias

cd python
uvicorn app.main:app --reload --port 8000
```

**Carga inicial.** `./scripts/seed.sh` roda `alembic upgrade head` e depois `python -m app.seed` (em `python/app/seed.py`), com o venv ativo. Ele cria os quatro usuários de demonstração (`admin`, `operador`, `gestor`, `auditor`, um por perfil) e as 11 categorias de [`dados-semente.md`](../modelo-de-dados/dados-semente.md). As senhas vêm das variáveis `SEED_*_PASSWORD` do `.env` (o `.env.example` traz valores didáticos); o script lê o `.env` da raiz, sem sobrepor variáveis já exportadas no shell. É idempotente e recusa rodar com `ENVIRONMENT=producao`. **Não carrega** os dados do pipeline (`dataset/processed/` e `dataset/synthetic/`): isso é a pendência D.9 do [`ROADMAP.md`](../ROADMAP.md). Sem eles, o banco local começa só com usuários e categorias; os ativos entram pela API ou pela importação de CSV (ver [`importacao.md`](importacao.md)).

Fora de `ENVIRONMENT=local` a aplicação se recusa a iniciar com a `SECRET_KEY` padrão (ver [`configuracao.md`](../spec/configuracao.md) §13.1); no Docker isso é sempre o caso, e a chave vem do `.env`.

O perfil local usa **SQLite**, sem necessidade de banco externo. O perfil Docker usa **PostgreSQL**. A seleção é feita pela variável `DATABASE_URL`.

*Revisado (item 13 da resolução de pendências da Sprint 2, de 2026-09-30, que levou a suíte inteira para PostgreSQL 16, local e no CI; resumo em [`ROADMAP.md`](../ROADMAP.md#sprint-2--responsabilidade-e-depreciação)):* o SQLite serve só para executar a aplicação. Os testes rodam sempre contra PostgreSQL 16 (ver [`testes.md`](testes.md)). No SQLite não existe o trigger de imutabilidade do histórico, o lock de linha da transferência nem a verificação de chave estrangeira (`PRAGMA foreign_keys` fica desligado): use o perfil Docker para verificar a imutabilidade (BR-011, AC-013) e a concorrência da transferência (BR-007).


## Portas publicadas pelo Docker Compose

O `docker-compose.yml` publica as quatro portas no host a partir de variáveis do `.env`, com o valor padrão entre parênteses:

| Variável | Serviço | Padrão |
|---|---|---|
| `API_PORT` | API (FastAPI) | 8000 |
| `DB_PORT` | PostgreSQL | 5432 |
| `PROMETHEUS_PORT` | Prometheus | 9090 |
| `GRAFANA_PORT` | Grafana | 3000 |

Se uma dessas portas já estiver ocupada na máquina (outro PostgreSQL, outra API), troque só o valor no `.env` e suba de novo:

```bash
# .env
API_PORT=18000
DB_PORT=15432

docker compose up -d
scripts/smoke_test.sh        # lê API_PORT, PROMETHEUS_PORT e GRAFANA_PORT do mesmo .env
```

A troca afeta apenas o lado do host. Dentro da rede do Compose, a API continua falando com o banco em `db:5432` e o Prometheus continua coletando de `api:8000`. Com `DB_PORT` alterado, a suíte de testes no host precisa da porta nova em `TEST_DATABASE_URL`, por exemplo `postgresql+psycopg://itam:itam@localhost:15432/itam_test`.

Isso mitiga o risco RI-10 (ambiente da apresentação falhar): conflito de porta deixa de exigir edição do `docker-compose.yml`. Se o Docker inteiro falhar, use o perfil SQLite descrito acima.
