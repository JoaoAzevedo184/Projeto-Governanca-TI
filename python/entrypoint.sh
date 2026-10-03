#!/bin/sh
# Inicialização do contêiner da API: aplica as migrações e só então sobe o servidor.
# `alembic upgrade head` é idempotente (sem migração pendente, não faz nada). Se falhar, ou se a
# configuração for recusada (SECRET_KEY padrão fora de `local`), o contêiner sai com a mensagem
# no log e o servidor nem chega a subir, então o healthcheck só passa depois da migração.
# O seed (usuários de demonstração) fica de fora, em scripts/seed.sh.
set -e
echo "Aplicando migrações (alembic upgrade head)..."
alembic upgrade head
echo "Iniciando a API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
