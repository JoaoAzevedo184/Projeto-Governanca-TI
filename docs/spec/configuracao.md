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
DATABASE_URL=sqlite:///./itam.db
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

Nenhum valor padrão de `SECRET_KEY` é aceito quando `ENVIRONMENT != local`: a aplicação deve **recusar a inicialização**, não apenas emitir aviso.

### 13.2 Migrações e carga inicial

- Alembic com uma migração por alteração de esquema, nunca `create_all()` em ambiente não local;
- `scripts/seed.sh` popula categorias com a vida útil padrão da tabela do FR-003, os quatro perfis de usuário e os datasets de demonstração;
- `scripts/reset.sh` derruba volumes e recria do zero — **somente em laboratório**.

