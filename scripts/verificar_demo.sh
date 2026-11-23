#!/usr/bin/env bash
# Confere, pela API, os 6 números do cenário de demonstração (python -m app.seed_demo), no dia em
# que roda. Imprime ✓/✗ por item e sai com código 1 se algum divergir. Um banco semeado em outro
# dia diverge (as datas do seed ficam gravadas): recrie o banco e semeie no dia da apresentação.
# URL e credenciais vêm do ambiente ou do .env (mesmos nomes do .env.example e do smoke_test.sh).
set -euo pipefail
cd "$(dirname "$0")/.."

# valor de uma variável: do ambiente, senão do .env
valor() {
  local v="${!1:-}"
  if [ -z "$v" ] && [ -f .env ]; then v="$(grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true)"; fi
  printf '%s' "$v"
}

porta_api="$(valor API_PORT)"
API="${API_URL:-http://localhost:${porta_api:-8000}}/api/v1"

senha="$(valor SEED_ADMIN_PASSWORD)"
[ -n "$senha" ] || { echo "SEED_ADMIN_PASSWORD não definida (ambiente ou .env)" >&2; exit 1; }
token="$(curl -sf -X POST "$API/auth/login" -H 'content-type: application/json' \
  -d "{\"login\":\"admin\",\"senha\":\"$senha\"}" | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')" \
  || { echo "login do admin falhou em $API (API no ar? seed básico executado?)" >&2; exit 1; }

get() { curl -sf "$API$1" -H "Authorization: Bearer $token"; }

serie_ac015="DEMO-HW-AC015"
id_ac015="$(get "/ativos?busca=$serie_ac015" | python3 -c '
import sys, json
itens = [a for a in json.load(sys.stdin)["itens"] if a["numero_serie"] == sys.argv[1]]
print(itens[0]["id"] if itens else "")' "$serie_ac015")"
depreciacao='{}'
[ -n "$id_ac015" ] && depreciacao="$(get "/ativos/$id_ac015/depreciacao")"

# Licenças: todas as páginas (tamanho máximo 100).
licencas="$(python3 - "$API" "$token" <<'PY'
import json, sys, urllib.request
api, token = sys.argv[1], sys.argv[2]
itens, pagina = [], 1
while True:
    req = urllib.request.Request(f"{api}/licencas?tamanho=100&pagina={pagina}",
                                 headers={"Authorization": f"Bearer {token}"})
    corpo = json.load(urllib.request.urlopen(req))  # nosec B310 (URL da própria API)
    itens += corpo["itens"]
    if pagina >= corpo["total_paginas"]:
        break
    pagina += 1
print(json.dumps(itens))
PY
)"
alertas="$(get /compliance/alertas)"
baixados="$(get "/ativos?status=BAIXADO&tamanho=1")"

python3 - "$depreciacao" "$licencas" "$alertas" "$baixados" <<'PY'
import json, sys
depreciacao, licencas, alertas, baixados = (json.loads(a) for a in sys.argv[1:5])
todos = [a for g in alertas["grupos"] for a in g["alertas"]]

def contar(cond):
    return sum(1 for item in licencas if cond(item))

itens = [
    ("residual R$ 4.800,00 no ativo do AC-015 (DEMO-HW-AC015)",
     depreciacao.get("valor_residual") == "4800.00",
     f"valor_residual={depreciacao.get('valor_residual')}, meses={depreciacao.get('meses_decorridos')}"),
    ("1 licença vencida há 40 dias",
     contar(lambda l: l["dias_para_expiracao"] == -40) == 1,
     f"{contar(lambda l: l['dias_para_expiracao'] == -40)} com dias_para_expiracao=-40"),
    ("1 licença a vencer em 25 dias",
     contar(lambda l: l["dias_para_expiracao"] == 25) == 1,
     f"{contar(lambda l: l['dias_para_expiracao'] == 25)} com dias_para_expiracao=25"),
    ("1 licença em 50 de 50",
     contar(lambda l: l["quantidade_contratada"] == 50 and l["quantidade_em_uso"] == 50) == 1,
     f"{contar(lambda l: l['quantidade_contratada'] == 50 and l['quantidade_em_uso'] == 50)} em 50 de 50"),
    ("3 ativos sem responsável (alertas CP-04)",
     sum(a["codigo"] == "CP-04" for a in todos) == 3,
     f"{sum(a['codigo'] == 'CP-04' for a in todos)} alertas CP-04"),
    ("1 ativo baixado",
     baixados["total"] == 1,
     f"{baixados['total']} com status BAIXADO"),
]
print(f"Data de referência da API: {alertas['data_referencia']}")
for descricao, ok, medido in itens:
    print(f"  {'✓' if ok else '✗'}  {descricao}" + ("" if ok else f"  (medido: {medido})"))
falhas = sum(not ok for _, ok, _ in itens)
if falhas:
    print(f"verificação da demonstração FALHOU: {falhas} de {len(itens)} itens divergem "
          "(banco semeado em outro dia? recrie e semeie hoje)")
    sys.exit(1)
print("verificação da demonstração OK")
PY
