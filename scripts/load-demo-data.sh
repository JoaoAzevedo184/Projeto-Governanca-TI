#!/usr/bin/env sh
set -eu
curl -fsS -X POST http://localhost:8101/api/v1/imports/events -F file=@datasets/alertas.csv;echo
