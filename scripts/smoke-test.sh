#!/usr/bin/env sh
set -eu
curl -fsS http://localhost:8101/api/v1/kpis
echo OK
