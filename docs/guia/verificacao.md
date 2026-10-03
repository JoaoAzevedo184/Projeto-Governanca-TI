# Guia — Verificando a Instalação

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Verificando a instalação

```bash
./scripts/smoke_test.sh
```

Sequência do zero: `./scripts/start.sh` (a API migra o banco ao iniciar) → esperar `docker compose ps` mostrar a API `healthy` → `./scripts/seed.sh` → `./scripts/smoke_test.sh`.

O script verifica, em sequência: `/health` (aplicação e banco `UP`), login do admin (exige o seed: `./scripts/seed.sh`), `GET /compliance/alertas`, `GET /indicadores`, `GET /relatorios/inventario?formato=csv`, as métricas `itam_*` em `/metrics`, o alvo `itam-api` do Prometheus em estado `up` e o dashboard `itam-tecnico` provisionado no Grafana. URLs e credenciais vêm do ambiente ou do `.env`. Saída diferente de zero indica ambiente incompleto.

Com o ambiente no ar, o contador de recusas se confere à mão: provoque uma recusa (por exemplo, dar baixa duas vezes no mesmo ativo) e veja `itam_regras_violadas_total{regra="BR-024"}` subir em `http://localhost:8000/metrics`.

Verificação manual mínima:

```bash
# 1. Autenticar
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"admin","senha":"admin"}' | jq -r .access_token)

# 2. Listar ativos
curl -s http://localhost:8000/api/v1/ativos \
  -H "Authorization: Bearer $TOKEN" | jq '.total'

# 3. Consultar indicadores
curl -s http://localhost:8000/api/v1/indicadores \
  -H "Authorization: Bearer $TOKEN" | jq '.indicadores[] | {codigo, nome, valor}'

# 4. Ver alertas de compliance
curl -s http://localhost:8000/api/v1/compliance/alertas \
  -H "Authorization: Bearer $TOKEN" | jq '.grupos[].alertas[] | {codigo, severidade, regra, recurso}'
```

