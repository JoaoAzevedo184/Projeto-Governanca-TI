# Guia — Verificando a Instalação

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Verificando a instalação

```bash
./scripts/smoke_test.sh
```

O script verifica, em sequência: health da API, disponibilidade do banco, endpoint de indicadores, endpoint de métricas, saúde do Prometheus e saúde do Grafana. Saída diferente de zero indica ambiente incompleto.

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
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {codigo, severidade, descricao}'
```

