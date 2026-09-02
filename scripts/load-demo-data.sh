#!/usr/bin/env sh
set -eu
for port in 8101 8102;do curl -fsS -X POST http://localhost:$port/api/v1/imports/events -F file=@datasets/alertas.csv;echo;done
