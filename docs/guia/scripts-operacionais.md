# Guia — Scripts Operacionais

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Scripts operacionais

| Script | Ação |
|---|---|
| `./scripts/start.sh` | Sobe todo o ambiente |
| `./scripts/stop.sh` | Encerra os contêineres preservando os dados |
| `./scripts/reset.sh` | Remove contêineres, redes e **volumes** — apaga os dados |
| `./scripts/seed.sh` | Carrega categorias, usuários e os datasets de `data/processed/` e `data/synthetic/` |
| `./scripts/collect.sh` | Executa coleta e normalização de todas as fontes públicas |
| `./scripts/smoke_test.sh` | Verifica se o ambiente subiu corretamente |

> `reset.sh` elimina dados persistidos. Use apenas em ambiente de laboratório.

Acompanhar logs:

```bash
docker compose logs -f              # todos os serviços
docker compose logs -f api          # apenas a API
```

