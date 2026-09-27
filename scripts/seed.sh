#!/usr/bin/env bash
set -euo pipefail
(cd python && alembic upgrade head)
