"""Datas injetáveis. `hoje()` é o único ponto que lê o relógio nos serviços de baixa e licença,
para o teste poder fixar a data sem mexer no relógio do sistema."""

from datetime import date


def hoje() -> date:
    return date.today()
