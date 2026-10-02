"""Depreciação linear (FR-003) — docs/spec/regras-de-calculo.md §7.1.

Função pura: sem sessão de banco e sem `date.today()`. A `data_referencia` é sempre
injetada por quem chama. Não há regra por tipo de ativo: HARDWARE e SOFTWARE depreciam
igual, pela vida útil herdada da categoria (BR-006, BR-013).

Arredondamento só no resultado final, como no PRD (FR-003; precedência pela ADR-013):
acumulada = valor × meses ÷ vida útil. A mensal é informativa e arredondada à parte, então
mensal × meses pode diferir da acumulada em centavos.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")


def _arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)  # BR-017


def meses_entre(inicio: date, fim: date) -> int:
    """Meses completos de `inicio` até `fim`; nunca negativo (fim antes do início = 0)."""
    meses = (fim.year - inicio.year) * 12 + (fim.month - inicio.month)
    if fim.day < inicio.day:
        meses -= 1
    return max(meses, 0)


@dataclass(frozen=True)
class Depreciacao:
    valor_compra: Decimal
    vida_util_meses: int
    meses_decorridos: int
    meses_efetivos: int
    depreciacao_mensal: Decimal
    depreciacao_acumulada: Decimal
    valor_residual: Decimal
    percentual_depreciado: Decimal


def calcular(
    valor_compra: Decimal, data_aquisicao: date, vida_util_meses: int, data_referencia: date
) -> Depreciacao:
    decorridos = meses_entre(data_aquisicao, data_referencia)
    efetivos = min(decorridos, vida_util_meses)
    mensal = _arredondar(valor_compra / Decimal(vida_util_meses))
    # efetivos ≤ vida útil: fecha exatamente no valor de compra ao fim da vida útil (BR-014).
    acumulada = _arredondar(valor_compra * efetivos / Decimal(vida_util_meses))
    residual = _arredondar(valor_compra - acumulada)
    percentual = _arredondar(acumulada / valor_compra * Decimal(100))
    return Depreciacao(
        valor_compra, vida_util_meses, decorridos, efetivos, mensal, acumulada, residual, percentual
    )
