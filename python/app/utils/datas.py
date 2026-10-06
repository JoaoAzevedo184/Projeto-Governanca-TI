"""Datas injetáveis. `hoje()` é o único ponto que lê o relógio nos serviços e nos schemas, para o
teste poder fixar a data sem mexer no relógio do sistema.

A data de referência do domínio ("hoje") usa o fuso `FUSO_HORARIO` (padrão America/Recife). Em UTC
o dia virava às 21h de Recife. Só a data de referência muda: os carimbos de tempo (`criado_em` e
semelhantes) seguem como estavam.
"""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def _agora_utc() -> datetime:
    """O relógio do domínio; os testes o substituem para controlar a virada de dia."""
    return datetime.now(UTC)


def hoje() -> date:
    return _agora_utc().astimezone(ZoneInfo(get_settings().fuso_horario)).date()


def agora() -> datetime:
    return datetime.now()
