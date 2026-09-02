#!/usr/bin/env sh
set -eu
for i in $(seq 1 60);do curl -fsS http://localhost:8101/health >/dev/null 2>&1&&exit 0;sleep 3;done;exit 1
