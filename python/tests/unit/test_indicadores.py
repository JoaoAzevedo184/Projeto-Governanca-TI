"""Fórmulas dos indicadores (FR-009): funções puras, esperado calculado à mão."""

from datetime import date
from decimal import Decimal

import pytest

from app.utils.indicadores import (
    atende_meta,
    custo_medio,
    idade_media_meses,
    percentual,
    percentual_depreciado_parque,
    sem_movimentacao,
)

REF = date(2026, 3, 20)


def test_percentual_arredonda_half_up_em_duas_casas():
    assert percentual(1, 3) == Decimal("33.33")
    assert percentual(2, 3) == Decimal("66.67")
    assert percentual(1, 8) == Decimal("12.50")
    assert percentual(0, 5) == Decimal("0.00")


def test_percentual_sem_amostra_nao_tem_valor():
    assert percentual(0, 0) is None


def test_percentual_depreciado_do_parque():
    # (1 - 7.500 / 10.000) * 100 = 25
    assert percentual_depreciado_parque(Decimal("10000"), Decimal("7500")) == Decimal("25.00")
    assert percentual_depreciado_parque(Decimal("0"), Decimal("0")) is None


def test_custo_medio():
    assert custo_medio(Decimal("10000"), 3) == Decimal("3333.33")
    assert custo_medio(Decimal("0"), 0) is None


def test_idade_media_em_meses_completos():
    # 12 meses (2025-03-20) e 6 meses (2025-09-20): média 9
    assert idade_media_meses([date(2025, 3, 20), date(2025, 9, 20)], REF) == Decimal("9.00")
    assert idade_media_meses([], REF) is None


@pytest.mark.parametrize(
    ("ultimo", "ocioso"),
    [
        (date(2025, 3, 20), False),  # exatamente 12 meses: ainda dentro do limite
        (date(2025, 3, 19), True),  # um dia além dos 12 meses
        (date(2025, 2, 20), True),  # 13 meses
        (date(2026, 3, 20), False),
    ],
)
def test_sem_movimentacao_acima_do_limite_em_meses(ultimo, ocioso):
    assert sem_movimentacao(ultimo, REF, 12) is ocioso


def test_sem_movimentacao_com_fim_de_mes_curto():
    # 2026-03-31 menos 1 mês = 2026-02-28 (fevereiro não tem dia 31)
    assert sem_movimentacao(date(2026, 2, 27), date(2026, 3, 31), 1) is True
    assert sem_movimentacao(date(2026, 2, 28), date(2026, 3, 31), 1) is False


@pytest.mark.parametrize(
    ("valor", "meta", "sentido", "esperado"),
    [
        (Decimal("98"), Decimal("98"), ">=", True),
        (Decimal("97.99"), Decimal("98"), ">=", False),
        (Decimal("10"), Decimal("10"), "<=", True),
        (Decimal("10.01"), Decimal("10"), "<=", False),
        (None, Decimal("98"), ">=", None),
        (Decimal("5"), None, None, None),
    ],
)
def test_atende_meta(valor, meta, sentido, esperado):
    assert atende_meta(valor, meta, sentido) is esperado
