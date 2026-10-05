"""Scorecard de fornecedores (FR-011, BR-029, AC-048, AC-049) — regras-de-calculo.md §7.4.

Funções puras com `Decimal`, sem banco e sem relógio. A pontuação arredonda só no resultado
final, em 2 casas, half-up (BR-017), como a depreciação. A soma dos pesos compara `Decimal`,
nunca `float`: 0,3 + 0,3 + 0,4 ≠ 1,0 em ponto flutuante binário.
"""

from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")
CEM = Decimal(100)


def soma_dos_pesos(pesos: Sequence[Decimal]) -> Decimal:
    return sum(pesos, Decimal(0))


def pesos_somam_100(pesos: Sequence[Decimal]) -> bool:
    """BR-029: os pesos totalizam exatamente 100%."""
    return soma_dos_pesos(pesos) == CEM


def pontuacao(notas: Mapping[str, Decimal], pesos: Mapping[str, Decimal]) -> Decimal:
    """Soma de `nota × peso ÷ 100` sobre os critérios, de 0 a 10, arredondada no fim."""
    total = sum((notas[criterio] * peso / CEM for criterio, peso in pesos.items()), Decimal(0))
    return total.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def ranking(pontuacoes: Mapping[int, Decimal]) -> list[tuple[int, int, Decimal]]:
    """`(posição, id, pontuação)` da maior para a menor pontuação. Empate: menor id primeiro, e as
    posições seguem a ordem da lista (1, 2, 3...), sem posição repetida."""
    ordenados = sorted(pontuacoes.items(), key=lambda item: (-item[1], item[0]))
    return [(posicao, ident, nota) for posicao, (ident, nota) in enumerate(ordenados, start=1)]
