#!/usr/bin/env bash
# Coleta as três fontes (Compras.gov.br, endoflife e NVD) em dataset/raw/<fonte>/<data>/ e normaliza.
# Precisa do ambiente virtual Python ativo (o script usa `python`):
#   source python/.venv/bin/activate     (ver docs/guia/preparo-da-demonstracao.md, passo 3)
# A coleta de hoje fica só em dataset/raw/. A etapa final regenera dataset/processed/ a partir das
# coletas de REFERÊNCIA (python/collectors/config.yaml, bloco `referencia`), nunca da de hoje, e é
# pulada com um aviso se essas coletas não estão em dataset/raw/. Ver docs/guia/coleta-de-dados.md.
set -euo pipefail
cd "$(dirname "$0")/../python"
if [ -z "${VIRTUAL_ENV:-}${CONDA_PREFIX:-}" ] || ! command -v python >/dev/null 2>&1; then
  echo "Erro: o ambiente virtual Python não está ativo (o script usa 'python', que só existe com ele)." >&2
  echo "Ative-o e rode de novo: source python/.venv/bin/activate (ver docs/guia/preparo-da-demonstracao.md, passo 3)." >&2
  exit 1
fi
python -m collectors.compras_gov
python -m collectors.endoflife
python -m collectors.nvd
python -m etl.normalizar --se-houver-referencia
