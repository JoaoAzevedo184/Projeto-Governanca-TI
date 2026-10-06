#!/usr/bin/env bash
# Carrega o seed de demonstração dos Gates 2 e 3 (python -m app.seed_demo). Pré-requisitos: seed
# básico (scripts/seed.sh) e os 92 ativos de dataset/demo/inventario_demo.csv importados
# (docs/guia/importacao.md); sem eles o script encerra com mensagem e não cria nada.
# Com a API do Docker Compose no ar, roda dentro do contêiner `api`; senão, no ambiente local
# (venv ativo, DATABASE_URL do .env). Força com SEED_MODE=docker|local.
set -euo pipefail
cd "$(dirname "$0")/.."

modo="${SEED_MODE:-}"
if [ -z "$modo" ]; then
  if docker compose ps --status running --services 2>/dev/null | grep -qx api; then
    modo=docker
  else
    modo=local
  fi
fi

if [ "$modo" = docker ]; then
  docker compose exec -T api python -m app.seed_demo
else
  # .env só preenche o que o shell ainda não definiu (variável exportada tem precedência)
  if [ -f .env ]; then
    while IFS='=' read -r chave valor; do
      case "$chave" in ''|\#*) continue ;; esac
      if [ -z "${!chave+x}" ]; then export "$chave=$valor"; fi
    done < .env
  fi
  # variável vazia no .env não pode sobrepor o padrão da aplicação
  [ -n "${DATABASE_URL:-}" ] || unset DATABASE_URL
  [ -n "${ENVIRONMENT:-}" ] || unset ENVIRONMENT
  cd python
  python -m app.seed_demo
fi
