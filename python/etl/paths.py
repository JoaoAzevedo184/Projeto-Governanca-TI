"""Resolução de DATASET_DIR compartilhada por collectors/ e etl/.

Fora de contêiner, o default é dataset/ na raiz do repositório (calculado a
partir deste arquivo, não do cwd). Em Docker, DATASET_DIR vem do
docker-compose.yml (montado em /dataset).
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = Path(os.getenv("DATASET_DIR", REPO_ROOT / "dataset"))
