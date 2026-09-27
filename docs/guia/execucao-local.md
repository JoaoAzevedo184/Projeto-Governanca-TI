# Guia — Execução Local sem Docker

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Execução local sem Docker

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env               # DATABASE_URL já aponta para SQLite

alembic upgrade head
python -m scripts.seed

uvicorn app.main:app --reload --port 8000
```

O perfil local usa **SQLite**, sem necessidade de banco externo. O perfil Docker usa **PostgreSQL**. A seleção é feita pela variável `DATABASE_URL`.

