# Guia — Scripts Operacionais

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Scripts operacionais

| Script | Ação |
|---|---|
| `./scripts/start.sh` | Confere a `SECRET_KEY` do `.env` (falha com mensagem clara se faltar ou for a padrão) e sobe todo o ambiente com `docker compose up -d`. A API migra o banco ao iniciar; o banco sobe vazio |
| `./scripts/stop.sh` | Encerra os contêineres preservando os dados |
| `./scripts/reset.sh` | Remove contêineres, redes e **volumes** — apaga os dados |
| `./scripts/seed.sh` | Rode **depois** de a API ficar saudável. Aplica as migrações (já aplicadas pelo start da API; idempotente) e carrega os quatro usuários de demonstração e as 11 categorias (`python -m app.seed`). Roda no contêiner `api` quando ele está no ar, senão no ambiente local (`SEED_MODE=docker\|local` força). Idempotente. **Não** carrega `dataset/processed/` nem `dataset/synthetic/` (pendência D.9) |
| `./scripts/collect.sh` | Executa coleta e normalização de todas as fontes públicas |
| `./scripts/smoke_test.sh` | Verifica se o ambiente subiu corretamente |

> `reset.sh` elimina dados persistidos. Use apenas em ambiente de laboratório.

Acompanhar logs:

```bash
docker compose logs -f              # todos os serviços
docker compose logs -f api          # apenas a API
```

