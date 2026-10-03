#!/usr/bin/env bash
# Smoke test do ambiente completo (docker compose up + scripts/seed.sh): API, banco, painel de
# compliance, indicadores, /metrics, alvo do Prometheus e dashboard do Grafana.
# URLs e credenciais vêm do ambiente ou do .env (mesmos nomes do .env.example).
set -euo pipefail
cd "$(dirname "$0")/.."

# valor de uma variável: do ambiente, senão do .env
valor() {
  local v="${!1:-}"
  if [ -z "$v" ] && [ -f .env ]; then v="$(grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true)"; fi
  printf '%s' "$v"
}

porta_prom="$(valor PROMETHEUS_PORT)"; porta_grafana="$(valor GRAFANA_PORT)"
API="${API_URL:-http://localhost:8000}"
PROM="${PROMETHEUS_URL:-http://localhost:${porta_prom:-9090}}"
GRAFANA="${GRAFANA_URL:-http://localhost:${porta_grafana:-3000}}"

passo() { printf '  ok  %s\n' "$1"; }
falha() { printf 'FALHOU  %s\n' "$1" >&2; exit 1; }
# repete o comando até dar certo (até 60 s): o ambiente pode ainda estar subindo
esperar() {
  local descricao="$1"; shift
  for _ in $(seq 1 30); do if "$@" >/dev/null 2>&1; then passo "$descricao"; return 0; fi; sleep 2; done
  falha "$descricao"
}

esperar "GET /health: aplicação e banco UP" \
  bash -c "curl -sf '$API/health' | grep -q '\"status\":\"UP\"' && curl -sf '$API/health' | grep -q '\"database\":{\"status\":\"UP\"'"

senha="$(valor SEED_ADMIN_PASSWORD)"
[ -n "$senha" ] || falha "SEED_ADMIN_PASSWORD não definida (ambiente ou .env); rode scripts/seed.sh antes"
token="$(curl -sf -X POST "$API/api/v1/auth/login" -H 'content-type: application/json' \
  -d "{\"login\":\"admin\",\"senha\":\"$senha\"}" | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')" \
  || falha "login do admin (o seed foi executado?)"
passo "login do admin"

for rota in /api/v1/compliance/alertas /api/v1/indicadores "/api/v1/relatorios/inventario?formato=csv"; do
  curl -sf "$API$rota" -H "Authorization: Bearer $token" >/dev/null || falha "GET $rota"
  passo "GET $rota"
done

metricas="$(curl -sf "$API/metrics")" || falha "GET /metrics"
for nome in itam_http_requests_total itam_regras_violadas_total itam_ativos_total itam_database_up; do
  grep -q "^# TYPE $nome " <<<"$metricas" || falha "/metrics sem $nome"
done
passo "GET /metrics expõe as métricas itam_*"

esperar "Prometheus: alvo itam-api UP" \
  bash -c "curl -sf '$PROM/api/v1/targets' | grep -q '\"health\":\"up\"'"

usuario="$(valor GRAFANA_USER)"; usuario="${usuario:-admin}"
senha_grafana="$(valor GRAFANA_PASSWORD)"; senha_grafana="${senha_grafana:-admin}"
esperar "Grafana: dashboard itam-tecnico provisionado" \
  bash -c "curl -sf -u '$usuario:$senha_grafana' '$GRAFANA/api/search?query=ITAM' | grep -q itam-tecnico"

echo "smoke test OK"
