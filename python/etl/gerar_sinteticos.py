"""Gera os dados sintéticos do ITAM pela API do Mockaroo (FR-002, FR-005).

Lê cada esquema em <DATASET_DIR>/synthetic/schemas/*.json e grava o CSV
correspondente em <DATASET_DIR>/synthetic/ (DATASET_DIR default: dataset/
na raiz do repositório). Os CSVs gerados devem ser versionados: o Mockaroo
não aceita semente fixa, então o arquivo commitado é a garantia de
reprodutibilidade do seed.

Uso (a partir de python/):
    python -m etl.gerar_sinteticos                 # todos os esquemas, 150 linhas
    python -m etl.gerar_sinteticos --linhas 300
    python -m etl.gerar_sinteticos --schema colaboradores
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

from etl.paths import DATASET_DIR

API_URL = "https://api.mockaroo.com/api/generate.csv"
DIR_SCHEMAS = DATASET_DIR / "synthetic" / "schemas"
DIR_SAIDA = DATASET_DIR / "synthetic"


def gerar(schema: Path, linhas: int, chave: str) -> Path:
    campos = json.loads(schema.read_text(encoding="utf-8"))
    resp = httpx.post(
        API_URL,
        params={"key": chave, "count": linhas},
        json=campos,
        timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"{schema.name}: HTTP {resp.status_code} — {resp.text[:300]}")

    destino = DIR_SAIDA / f"{schema.stem}.csv"
    destino.write_text(resp.text, encoding="utf-8")
    return destino


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Gera CSVs sintéticos via Mockaroo")
    parser.add_argument("--linhas", type=int, default=150)
    parser.add_argument("--schema", help="nome do esquema, sem .json (padrão: todos)")
    args = parser.parse_args()

    chave = os.getenv("MOCKAROO_API_KEY")
    if not chave:
        print("Defina MOCKAROO_API_KEY no .env", file=sys.stderr)
        return 1

    schemas = (
        [DIR_SCHEMAS / f"{args.schema}.json"] if args.schema else sorted(DIR_SCHEMAS.glob("*.json"))
    )
    if not schemas or not all(s.exists() for s in schemas):
        print(f"Nenhum esquema encontrado em {DIR_SCHEMAS}", file=sys.stderr)
        return 1

    DIR_SAIDA.mkdir(parents=True, exist_ok=True)
    for schema in schemas:
        destino = gerar(schema, args.linhas, chave)
        print(f"ok  {schema.stem:<20} -> {destino} ({args.linhas} linhas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())