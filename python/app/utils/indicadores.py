"""Fórmulas dos indicadores de ITAM (FR-009, KPIs do PRD §visao-geral).

Funções puras: recebem contagens e somas já apuradas e devolvem o valor, sem sessão de banco e
sem `date.today()` (a `data_referencia` é injetada). Percentuais em `Decimal`, 2 casas, half-up
(BR-017). Denominador zero devolve `None`: indicador sem amostra não tem valor.
"""

from calendar import monthrange
from collections.abc import Iterable
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.utils.depreciacao import CENTAVO, meses_entre


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def percentual(parte: int | Decimal, total: int | Decimal) -> Decimal | None:
    if not total:
        return None
    return _q(Decimal(parte) * 100 / Decimal(total))


def percentual_depreciado_parque(bruto: Decimal, residual: Decimal) -> Decimal | None:
    """(1 − residual / bruto) × 100."""
    if not bruto:
        return None
    return _q((1 - residual / bruto) * 100)


def custo_medio(bruto: Decimal, quantidade: int) -> Decimal | None:
    return _q(bruto / quantidade) if quantidade else None


def idade_media_meses(datas_aquisicao: Iterable[date], data_referencia: date) -> Decimal | None:
    meses = [meses_entre(d, data_referencia) for d in datas_aquisicao]
    return _q(Decimal(sum(meses)) / len(meses)) if meses else None


def _menos_meses(data: date, meses: int) -> date:
    indice = data.year * 12 + data.month - 1 - meses
    ano, mes = divmod(indice, 12)
    return date(ano, mes + 1, min(data.day, monthrange(ano, mes + 1)[1]))


def sem_movimentacao(ultimo_evento: date, data_referencia: date, meses_limite: int) -> bool:
    """Ocioso: o último evento é anterior a `meses_limite` meses antes da data de referência."""
    return ultimo_evento < _menos_meses(data_referencia, meses_limite)


def atende_meta(valor: Decimal | None, meta: Decimal | None, sentido: str | None) -> bool | None:
    """`sentido` `>=` ou `<=`. Sem valor ou sem meta, não há veredito."""
    if valor is None or meta is None or sentido is None:
        return None
    return valor >= meta if sentido == ">=" else valor <= meta
