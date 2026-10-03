"""Conformidade de licença (FR-004, FR-007): função pura, data de referência injetada."""

from datetime import date, timedelta

import pytest

from app.utils.conformidade import (
    ALERTA,
    CONFORME,
    NAO_CONFORME,
    REGRAS,
    SEVERIDADES,
    alertas_licenca,
    dias_para_expiracao,
    status_conformidade,
)

REF = date(2026, 3, 20)


def _alertas(contratada=10, em_uso=5, dias=100, janela=30):
    return alertas_licenca(contratada, em_uso, REF + timedelta(days=dias), REF, janela)


def test_dias_para_expiracao_e_negativo_quando_vencida():
    assert dias_para_expiracao(REF + timedelta(days=22), REF) == 22
    assert dias_para_expiracao(REF - timedelta(days=3), REF) == -3


@pytest.mark.parametrize(
    ("dias", "esperado"),
    [
        (-1, ["CP-01"]),  # venceu ontem
        (0, ["CP-03"]),  # vence hoje: ainda não venceu
        (25, ["CP-03"]),  # AC-022
        (30, ["CP-03"]),  # limite da janela, inclusive
        (31, []),
    ],
)
def test_cp01_e_cp03_pela_data_de_expiracao(dias, esperado):
    assert _alertas(dias=dias) == esperado


@pytest.mark.parametrize(
    ("em_uso", "esperado"), [(9, []), (10, []), (11, ["CP-02"]), (50, ["CP-02"])]
)
def test_cp02_so_quando_o_uso_excede_o_contratado(em_uso, esperado):
    assert _alertas(contratada=10, em_uso=em_uso) == esperado


def test_janela_de_alerta_e_configuravel():
    assert _alertas(dias=45, janela=30) == []
    assert _alertas(dias=45, janela=60) == ["CP-03"]


def test_licenca_pode_disparar_mais_de_um_alerta():
    assert _alertas(contratada=1, em_uso=2, dias=-5) == ["CP-01", "CP-02"]


@pytest.mark.parametrize(
    ("codigos", "esperado"),
    [
        ([], CONFORME),
        (["CP-03"], ALERTA),
        (["CP-01"], NAO_CONFORME),
        (["CP-02"], NAO_CONFORME),
        (["CP-02", "CP-03"], NAO_CONFORME),
    ],
)
def test_status_conformidade_resume_a_severidade_mais_alta(codigos, esperado):
    assert status_conformidade(codigos) == esperado


def test_catalogo_das_regras_traz_severidade_do_prd():
    assert {c: r.severidade for c, r in REGRAS.items()} == {
        "CP-01": "CRITICO",
        "CP-02": "CRITICO",
        "CP-03": "ALTO",
        "CP-04": "ALTO",
    }
    assert SEVERIDADES == ("CRITICO", "ALTO", "MEDIO", "BAIXO")
