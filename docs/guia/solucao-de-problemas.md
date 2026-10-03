# Guia — Solução de Problemas

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Solução de problemas

| Sintoma | Causa provável | Correção |
|---|---|---|
| `docker compose up` falha na porta 8000 | Porta ocupada | Altere `API_PORT` no `.env` |
| API sobe mas `/health` retorna `503` e banco `DOWN` | Postgres ainda inicializando | Aguarde o health check; verifique `docker compose logs db` |
| `alembic upgrade head` falha | `DATABASE_URL` incorreta | Confira o `.env`; em Docker o host é `db`, não `localhost` |
| Aplicação recusa iniciar com erro de `SECRET_KEY` | Chave padrão fora do ambiente local | Defina `SECRET_KEY` própria quando `ENVIRONMENT != local` |
| Importação retorna 422 antes de processar | Cabeçalhos divergentes | Compare com `dataset/demo/inventario_demo.csv` |
| Grafana sem dados | Prometheus não alcança a API | Verifique `infra/prometheus.yml` e `docker compose logs prometheus` |
| Testes falham só em PostgreSQL | Índice parcial ou trigger ausente | Rode `alembic upgrade head` no banco de teste |
| HTTP 403 em operação esperada | Perfil sem permissão | Consulte a matriz do FR-015 no PRD |
| Coletor `compras_gov` recebe 404 | Parâmetro obrigatório ausente na consulta | Confira os parâmetros do endpoint no Swagger do Compras.gov |
| Coletor `nvd` recebe 403 ou 429 | Limite de requisições excedido | Defina `NVD_API_KEY` no `.env` e execute novamente |
| Seed carrega poucos ativos | `dataset/processed/` vazio ou desatualizado | Rode `./scripts/collect.sh` ou restaure os arquivos do repositório |

