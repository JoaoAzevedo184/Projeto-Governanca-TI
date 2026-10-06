"""Data de referência do domínio ("hoje") no fuso configurado, padrão America/Recife.

Em UTC o dia virava às 21h de Recife. O relógio é controlado: `datas._agora_utc` devolve o instante
que o teste escolhe, então a virada de dia se testa sem depender da hora real.
"""

from datetime import UTC, date, datetime

import pytest

from app.core.config import ConfiguracaoInvalidaError, Settings, get_settings, validar_configuracao
from app.utils import datas


@pytest.fixture(autouse=True)
def _fuso_padrao(monkeypatch):
    monkeypatch.delenv("FUSO_HORARIO", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _relogio(monkeypatch, instante_utc: datetime) -> None:
    monkeypatch.setattr(datas, "_agora_utc", lambda: instante_utc)


def test_o_fuso_padrao_e_america_recife():
    assert Settings().fuso_horario == "America/Recife"


def test_as_22h_de_recife_a_data_e_a_de_recife_e_nao_a_do_utc(monkeypatch):
    # 22h de 10/03 em Recife (UTC-3) são 01h de 11/03 em UTC
    _relogio(monkeypatch, datetime(2031, 3, 11, 1, 0, tzinfo=UTC))

    assert datas.hoje() == date(2031, 3, 10)
    assert datetime(2031, 3, 11, 1, 0, tzinfo=UTC).date() == date(2031, 3, 11)  # o UTC já virou


def test_as_2h_de_recife_os_dois_fusos_coincidem(monkeypatch):
    # 02h de 11/03 em Recife são 05h de 11/03 em UTC
    _relogio(monkeypatch, datetime(2031, 3, 11, 5, 0, tzinfo=UTC))

    assert datas.hoje() == date(2031, 3, 11) == datetime(2031, 3, 11, 5, 0, tzinfo=UTC).date()


@pytest.mark.parametrize(
    ("instante", "esperado"),
    [
        (datetime(2031, 3, 11, 2, 59, 59, tzinfo=UTC), date(2031, 3, 10)),  # 23h59min59s em Recife
        (datetime(2031, 3, 11, 3, 0, 0, tzinfo=UTC), date(2031, 3, 11)),  # meia-noite em Recife
        (datetime(2031, 12, 31, 23, 0, tzinfo=UTC), date(2031, 12, 31)),  # 20h: virada do ano
        (datetime(2032, 1, 1, 2, 30, tzinfo=UTC), date(2031, 12, 31)),  # 23h30 de 31/12 em Recife
        (datetime(2032, 1, 1, 3, 0, tzinfo=UTC), date(2032, 1, 1)),
    ],
)
def test_a_virada_de_dia_e_a_meia_noite_de_recife(monkeypatch, instante, esperado):
    _relogio(monkeypatch, instante)

    assert datas.hoje() == esperado


def test_o_fuso_e_configuravel_por_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("FUSO_HORARIO", "UTC")
    get_settings.cache_clear()
    _relogio(monkeypatch, datetime(2031, 3, 11, 1, 0, tzinfo=UTC))

    assert datas.hoje() == date(2031, 3, 11)  # em UTC, o mesmo instante já é o dia 11


def test_fuso_desconhecido_e_recusado_na_configuracao(monkeypatch):
    configuracao = Settings(fuso_horario="America/Atlantida")

    with pytest.raises(ConfiguracaoInvalidaError, match="America/Atlantida"):
        validar_configuracao(configuracao)


def test_fuso_conhecido_passa_na_validacao():
    validar_configuracao(Settings(fuso_horario="America/Recife"))
    validar_configuracao(Settings(fuso_horario="UTC"))


def test_o_relogio_real_devolve_um_instante_com_fuso_utc():
    agora = datas._agora_utc()

    assert agora.tzinfo is not None and agora.utcoffset().total_seconds() == 0
