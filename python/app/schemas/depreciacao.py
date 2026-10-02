from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class DepreciacaoResponse(BaseModel):
    """Resposta de `GET /ativos/{id}/depreciacao` e bloco `depreciacao` do ativo (contrato §6.3).

    `meses_efetivos` e `depreciacao_mensal` expostos de propósito: cálculo auditável (AC-015).
    Valores monetários saem como string decimal, sem perda de precisão (contrato §6.3).
    """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ativo_id": 12,
                    "data_referencia": "2026-03-14",
                    "metodo": "LINEAR",
                    "valor_compra": "6000.00",
                    "vida_util_meses": 60,
                    "meses_decorridos": 12,
                    "meses_efetivos": 12,
                    "depreciacao_mensal": "100.00",
                    "depreciacao_acumulada": "1200.00",
                    "valor_residual": "4800.00",
                    "percentual_depreciado": "20.00",
                }
            ]
        }
    }

    ativo_id: int
    data_referencia: date
    metodo: Literal["LINEAR"] = "LINEAR"
    valor_compra: Decimal
    vida_util_meses: int
    meses_decorridos: int
    meses_efetivos: int
    depreciacao_mensal: Decimal = Field(
        description="Informativa: valor_compra ÷ vida_util_meses, arredondada (BR-017). "
        "A acumulada é valor_compra × meses_efetivos ÷ vida_util_meses, arredondada só no "
        "fim; mensal × meses pode diferir dela em centavos."
    )
    depreciacao_acumulada: Decimal
    valor_residual: Decimal
    percentual_depreciado: Decimal
