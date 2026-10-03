"""O `api/openapi.yaml` versionado é o contrato do app: não descreve rota que não existe nem
deixa de descrever rota que existe. Regenerar com o app (ver docs/guia/contribuicao.md)."""

import json
from pathlib import Path

import yaml

from app.main import app

ARQUIVO = Path(__file__).resolve().parents[2] / "api" / "openapi.yaml"


def test_openapi_yaml_e_igual_ao_gerado_pelo_app():
    versionado = yaml.safe_load(ARQUIVO.read_text(encoding="utf-8"))
    gerado = json.loads(json.dumps(app.openapi()))

    assert sorted(versionado["paths"]) == sorted(gerado["paths"])
    assert versionado == gerado


def test_rotas_fora_do_mvp_nao_estao_no_contrato():
    caminhos = set(yaml.safe_load(ARQUIVO.read_text(encoding="utf-8"))["paths"])

    assert not {c for c in caminhos if c.startswith("/api/v1/relatorios/")} - {
        "/api/v1/relatorios/inventario",
        "/api/v1/relatorios/conformidade",
    }
