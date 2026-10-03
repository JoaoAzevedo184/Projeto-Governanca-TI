#!/usr/bin/env bash
# Sobe o ambiente completo. O Compose roda a API com ENVIRONMENT=docker, que exige uma
# SECRET_KEY própria (docs/spec/configuracao.md §13.1): confere antes, com mensagem clara.
set -euo pipefail
cd "$(dirname "$0")/.."

chave="${SECRET_KEY:-}"
if [ -z "$chave" ] && [ -f .env ]; then
  chave="$(grep -E '^SECRET_KEY=' .env | tail -1 | cut -d= -f2- || true)"
fi
case "$chave" in
  ""|troque-esta-chave|troque-esta-chave-em-qualquer-ambiente-real)
    cat >&2 <<'MSG'
SECRET_KEY ausente ou padrão: a API se recusa a iniciar com ela fora de ENVIRONMENT=local.
Gere uma chave própria e coloque no .env (nunca no docker-compose.yml):

  python3 -c "import secrets; print(secrets.token_urlsafe(64))"

  SECRET_KEY=<a chave gerada>
MSG
    exit 1
    ;;
esac

docker compose up -d
