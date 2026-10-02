# SPEC — Configuração

Parte de [SPEC — ITAM](README.md).

## 13. Configuração

### 13.1 `.env.example`

```dotenv
# Aplicação
APP_NAME=ITAM
APP_VERSION=1.0.0
ENVIRONMENT=local              # local | docker | producao
LOG_LEVEL=INFO
API_PREFIX=/api/v1

# Banco
DATABASE_URL=sqlite:///./itam.db  # só execução local sem Docker; testes usam TEST_DATABASE_URL (PostgreSQL)
# DATABASE_URL=postgresql+psycopg://itam:itam@db:5432/itam_db

# Segurança
SECRET_KEY=troque-esta-chave-em-qualquer-ambiente-real
JWT_ALGORITHM=HS256
JWT_EXPIRACAO_MINUTOS=480
CORS_ORIGINS=http://localhost:3000

# Regras de negócio configuráveis
JANELA_ALERTA_LICENCA_DIAS=30
LIMIAR_FIM_VIDA_UTIL_PERCENTUAL=80
DIAS_MANUTENCAO_ALERTA=90
MESES_SEM_MOVIMENTACAO_ALERTA=12

# Importação
IMPORTACAO_TAMANHO_MAX_MB=5
IMPORTACAO_LINHAS_MAX=5000
```

*SQLite revisado (item 13 de [`RESOLUCAO_PENDENCIAS_SPRINT2.md`](../RESOLUCAO_PENDENCIAS_SPRINT2.md)):* `DATABASE_URL` em SQLite serve só para executar a aplicação sem Docker. A suíte de testes ignora `DATABASE_URL` e usa `TEST_DATABASE_URL`, que precisa apontar para um banco PostgreSQL `*_test` (`tests/conftest.py`).

Nenhum valor padrão de `SECRET_KEY` é aceito quando `ENVIRONMENT != local`: a aplicação deve **recusar a inicialização**, não apenas emitir aviso.

### 13.2 Migrações e carga inicial

- Alembic com uma migração por alteração de esquema, nunca `create_all()` em ambiente não local;
- `scripts/seed.sh` aplica as migrações e roda `python -m app.seed` (`app/seed.py`): popula as categorias com a vida útil padrão da tabela do FR-003 e os quatro usuários de demonstração, com senhas de `SEED_<PERFIL>_PASSWORD`. É idempotente e recusa `ENVIRONMENT=producao`. A carga dos datasets de demonstração (`dataset/processed/`, `dataset/synthetic/`) ainda não está integrada (D.9);
- `scripts/reset.sh` derruba volumes e recria do zero — **somente em laboratório**.

