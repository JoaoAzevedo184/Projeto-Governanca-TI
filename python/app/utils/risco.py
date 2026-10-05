"""Score e classificação de risco (FR-012, AC-050) — docs/spec/regras-de-calculo.md §7.3.

Funções puras, sem banco e sem relógio. O banco também calcula o `score` (coluna gerada), e os
dois têm de concordar: a mesma conta, em inteiros, sem arredondamento.
"""

from app.models.enums import ClassificacaoRisco

# (mínimo, máximo) inclusivos de cada faixa do PRD: 1–4 baixo, 5–9 médio, 10–14 alto, 15–25 crítico.
FAIXAS: dict[ClassificacaoRisco, tuple[int, int]] = {
    ClassificacaoRisco.BAIXO: (1, 4),
    ClassificacaoRisco.MEDIO: (5, 9),
    ClassificacaoRisco.ALTO: (10, 14),
    ClassificacaoRisco.CRITICO: (15, 25),
}


def calcular_score(probabilidade: int, impacto: int) -> int:
    return probabilidade * impacto


def classificar(score: int) -> ClassificacaoRisco:
    for classificacao, (minimo, maximo) in FAIXAS.items():
        if minimo <= score <= maximo:
            return classificacao
    raise ValueError(f"score fora de 1 a 25: {score}")
