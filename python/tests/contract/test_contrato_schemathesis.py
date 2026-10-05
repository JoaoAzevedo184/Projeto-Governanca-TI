"""Testes de contrato (docs/spec/estrategia-de-testes.md): o schemathesis gera requisições a partir
do `api/openapi.yaml` e valida cada resposta do app contra o contrato, em todas as operações.

Roda contra o app real (ASGI) e o PostgreSQL de teste, sem mock. As rotas protegidas recebem o
token de um ADMIN, porque o contrato de rota autenticada só se exercita autenticado.
"""

import os
from pathlib import Path

import schemathesis
import yaml
from hypothesis import HealthCheck, settings
from schemathesis.specs.openapi.checks import negative_data_rejection, positive_data_acceptance

from app.main import app

ARQUIVO = Path(__file__).resolve().parents[2] / "api" / "openapi.yaml"
EXEMPLOS = int(os.environ.get("CONTRATO_EXEMPLOS", "10"))

# Fora de propósito: uma API de regras de negócio recusa com 404/409 dados que são válidos pelo
# schema (id que não existe, número de série repetido), então "positive_data_acceptance" só gera
# ruído; e "negative_data_rejection" acusa a coerção permissiva do Pydantic (`0` aceito como
# booleano), que está documentada nos achados da Sprint 5 e não é trocada por modo estrito, para
# não quebrar a entrada de dinheiro como string.
EXCLUIDAS = [positive_data_acceptance, negative_data_rejection]

schema = schemathesis.openapi.from_dict(yaml.safe_load(ARQUIVO.read_text(encoding="utf-8")))
schema.app = app


@schema.parametrize()
@settings(
    max_examples=EXEMPLOS,
    deadline=None,
    suppress_health_check=list(HealthCheck),
    derandomize=True,  # mesma semente em toda execução: o CI não oscila
)
def test_contrato_da_api(case, token_admin):
    case.call_and_validate(
        headers={"Authorization": f"Bearer {token_admin}"}, excluded_checks=EXCLUIDAS
    )
