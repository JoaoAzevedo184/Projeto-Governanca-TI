"""TCO de cenários (FR-010, BR-028, AC-052) — docs/spec/regras-de-calculo.md §7.5.

Funções puras com `Decimal`, sem banco e sem relógio. Valores em 2 casas, half-up (BR-017), só no
resultado final. A função de ordenação ordena e nunca escolhe: devolve a lista inteira, sem marca
de vencedor (BR-028).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

HORIZONTE_ANOS = 5
CENTAVO = Decimal("0.01")


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class EntradaCenario:
    nome: str
    capex: Decimal
    opex_anual: Decimal
    score_risco: int


@dataclass(frozen=True)
class ResultadoCenario:
    nome: str
    capex: Decimal
    opex_anual: Decimal
    tco_5_anos: Decimal
    custo_por_ativo_ano: Decimal | None
    economia_vs_baseline: Decimal
    score_risco: int


def tco(capex: Decimal, opex_anual: Decimal, horizonte_anos: int = HORIZONTE_ANOS) -> Decimal:
    """`capex + opex_anual × horizonte`."""
    return _q(capex + opex_anual * horizonte_anos)


def custo_por_ativo_ano(
    tco_total: Decimal, quantidade_ativos: int, horizonte_anos: int = HORIZONTE_ANOS
) -> Decimal | None:
    """`tco ÷ (ativos × horizonte)`; sem ativos não há custo por ativo."""
    if quantidade_ativos <= 0:
        return None
    return _q(tco_total / (quantidade_ativos * horizonte_anos))


def escolher_baseline(nomes: Sequence[str]) -> str:
    """`MANTER` quando presente (o que acontece se nada mudar); senão o primeiro informado."""
    return "MANTER" if "MANTER" in nomes else nomes[0]


def comparar(
    entradas: Sequence[EntradaCenario], quantidade_ativos: int, baseline: str
) -> list[ResultadoCenario]:
    """Calcula cada cenário e devolve **ordenados** por TCO e depois por score de risco, ambos
    crescentes (menor é melhor), com o nome como último desempate. Nenhum é marcado como escolhido:
    a decisão é humana e se registra à parte (BR-028, FR-013)."""
    tcos = {e.nome: tco(e.capex, e.opex_anual) for e in entradas}
    base = tcos[baseline]
    resultados = [
        ResultadoCenario(
            nome=e.nome,
            capex=_q(e.capex),
            opex_anual=_q(e.opex_anual),
            tco_5_anos=tcos[e.nome],
            custo_por_ativo_ano=custo_por_ativo_ano(tcos[e.nome], quantidade_ativos),
            economia_vs_baseline=_q(base - tcos[e.nome]),
            score_risco=e.score_risco,
        )
        for e in entradas
    ]
    return sorted(resultados, key=lambda r: (r.tco_5_anos, r.score_risco, r.nome))
