#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../python"
python -m collectors.compras_gov
python -m collectors.endoflife
python -m collectors.nvd
python -m etl
