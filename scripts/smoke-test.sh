#!/usr/bin/env sh
set -eu
curl -fsS http://localhost:8101/api/v1/kpis
curl -fsS http://localhost:8102/api/v1/kpis
echo OK
