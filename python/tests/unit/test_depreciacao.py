"""Depreciação linear como função pura (FR-003, docs/spec/regras-de-calculo.md §7.1)."""

from datetime import date
from decimal import Decimal

import pytest

from app.utils.depreciacao import calcular, meses_entre

AQUISICAO = date(2025, 3, 14)


def test_ac015_depreciacao_de_6000_em_60_meses_apos_12_meses():
    resultado = calcular(Decimal("6000.00"), AQUISICAO, 60, date(2026, 3, 14))

    assert resultado.meses_decorridos == 12
    assert resultado.meses_efetivos == 12
    assert resultado.depreciacao_mensal == Decimal("100.00")
    assert resultado.depreciacao_acumulada == Decimal("1200.00")
    assert resultado.valor_residual == Decimal("4800.00")
    assert resultado.percentual_depreciado == Decimal("20.00")


def test_ac016_ativo_com_72_meses_e_vida_util_de_60_esta_totalmente_depreciado():
    resultado = calcular(Decimal("6000.00"), AQUISICAO, 60, date(2031, 3, 14))

    assert resultado.meses_decorridos == 72
    assert resultado.meses_efetivos == 60
    assert resultado.valor_residual == Decimal("0.00")
    assert resultado.percentual_depreciado == Decimal("100.00")


@pytest.mark.parametrize(
    ("valor", "vida_util"),
    [("100.00", 3), ("1000.00", 60), ("1000.00", 7), ("0.01", 60), ("99999.99", 36)],
)
@pytest.mark.parametrize("meses_de_uso", [0, 1, 2, 3, 6, 7, 35, 36, 59, 60, 61, 120])
def test_ac017_valor_residual_nunca_e_negativo(valor, vida_util, meses_de_uso):
    ano, mes = divmod(AQUISICAO.month - 1 + meses_de_uso, 12)
    referencia = date(AQUISICAO.year + ano, mes + 1, AQUISICAO.day)

    resultado = calcular(Decimal(valor), AQUISICAO, vida_util, referencia)

    assert resultado.valor_residual >= 0
    assert resultado.depreciacao_acumulada <= resultado.valor_compra
    assert resultado.valor_residual + resultado.depreciacao_acumulada == resultado.valor_compra


def test_calculo_usa_a_data_de_referencia_injetada_e_nao_a_data_corrente():
    # Pré-requisito do AC-019 (Sprint 3): o serviço injetará baixa.data_baixa (BR-015). Sem o
    # prefixo test_ac019 porque o critério em si só é verificável com baixa_ativo; ver ROADMAP.
    data_baixa = date(2026, 3, 14)

    na_baixa = calcular(Decimal("6000.00"), AQUISICAO, 60, data_baixa)
    hoje = calcular(Decimal("6000.00"), AQUISICAO, 60, date(2027, 3, 14))

    assert na_baixa.depreciacao_acumulada == Decimal("1200.00")  # 6.000,00 × 12 ÷ 60
    assert hoje.depreciacao_acumulada == Decimal("2400.00")  # 6.000,00 × 24 ÷ 60


def test_ac020_vidas_uteis_distintas_depreciam_proporcionalmente():
    referencia = date(2026, 3, 14)

    sessenta = calcular(Decimal("6000.00"), AQUISICAO, 60, referencia)
    trinta_e_seis = calcular(Decimal("6000.00"), AQUISICAO, 36, referencia)

    assert sessenta.depreciacao_acumulada == Decimal("1200.00")  # 6.000,00 × 12 ÷ 60
    # Arredonda só no fim (PRD, ADR-013): 6.000,00 × 12 ÷ 36 = 2.000,00. Arredondar a mensal
    # antes (166,67 × 12) daria 2.000,04. A mensal exposta é informativa.
    assert trinta_e_seis.depreciacao_mensal == Decimal("166.67")
    assert trinta_e_seis.depreciacao_acumulada == Decimal("2000.00")
    razao = trinta_e_seis.depreciacao_acumulada / sessenta.depreciacao_acumulada
    assert abs(razao - Decimal(60) / 36) < Decimal("0.0001")


def test_fim_da_vida_util_zera_residual_mesmo_com_mensal_arredondada_para_baixo():
    # 100,00 × 3 ÷ 3 = 100,00 (BR-014), embora a mensal informativa 33,33 × 3 dê 99,99.
    resultado = calcular(Decimal("100.00"), AQUISICAO, 3, date(2025, 6, 14))

    assert resultado.depreciacao_mensal == Decimal("33.33")
    assert resultado.depreciacao_acumulada == Decimal("100.00")
    assert resultado.valor_residual == Decimal("0.00")
    assert resultado.percentual_depreciado == Decimal("100.00")


def test_mensal_arredondada_para_cima_nao_ultrapassa_valor_de_compra():
    # 1.000,00 × 60 ÷ 60 = 1.000,00, embora a mensal informativa 16,67 × 60 dê 1.000,20.
    resultado = calcular(Decimal("1000.00"), AQUISICAO, 60, date(2030, 3, 14))

    assert resultado.depreciacao_acumulada == Decimal("1000.00")
    assert resultado.valor_residual == Decimal("0.00")


def test_referencia_anterior_a_aquisicao_nao_deprecia():
    resultado = calcular(Decimal("6000.00"), AQUISICAO, 60, date(2024, 1, 1))

    assert resultado.meses_decorridos == 0
    assert resultado.depreciacao_acumulada == Decimal("0.00")
    assert resultado.valor_residual == Decimal("6000.00")
    assert resultado.percentual_depreciado == Decimal("0.00")


def test_arredondamento_half_up_em_duas_casas():
    # Mensal: 1.000,00 ÷ 7 = 142,857… → 142,86 (BR-017).
    # Acumulada em 3 meses: 1.000,00 × 3 ÷ 7 = 428,571… → 428,57 (não 142,86 × 3 = 428,58).
    resultado = calcular(Decimal("1000.00"), AQUISICAO, 7, date(2025, 6, 14))

    assert resultado.depreciacao_mensal == Decimal("142.86")
    assert resultado.depreciacao_acumulada == Decimal("428.57")
    assert resultado.valor_residual == Decimal("571.43")  # 1.000,00 − 428,57
    assert resultado.percentual_depreciado == Decimal("42.86")  # 428,57 ÷ 1.000,00 × 100


def test_empate_exato_arredonda_para_cima_e_nao_para_o_par():
    # BR-017: 100,10 × 1 ÷ 4 = 25,025 → 25,03 (half-up). Half-even daria 25,02.
    resultado = calcular(Decimal("100.10"), AQUISICAO, 4, date(2025, 4, 14))

    assert resultado.depreciacao_mensal == Decimal("25.03")
    assert resultado.depreciacao_acumulada == Decimal("25.03")
    assert resultado.valor_residual == Decimal("75.07")  # 100,10 − 25,03


def test_arredonda_half_up_no_resultado_final_e_nao_na_mensal():
    # 100,00 × 2 ÷ 3 = 66,666… → 66,67. Arredondando a mensal antes: 33,33 × 2 = 66,66.
    resultado = calcular(Decimal("100.00"), AQUISICAO, 3, date(2025, 5, 14))

    assert resultado.depreciacao_acumulada == Decimal("66.67")
    assert resultado.valor_residual == Decimal("33.33")


@pytest.mark.parametrize(
    ("inicio", "fim", "esperado"),
    [
        (date(2025, 1, 31), date(2025, 2, 28), 0),  # mês incompleto
        (date(2025, 1, 31), date(2025, 3, 31), 2),
        (date(2025, 1, 15), date(2025, 2, 14), 0),
        (date(2025, 1, 15), date(2025, 2, 15), 1),
        (date(2024, 2, 29), date(2025, 2, 28), 11),  # ano bissexto
        (date(2025, 12, 10), date(2026, 1, 10), 1),  # virada de ano
        (date(2025, 3, 14), date(2025, 3, 14), 0),
        (date(2025, 3, 14), date(2025, 1, 1), 0),  # fim antes do início
    ],
)
def test_meses_entre_conta_meses_completos(inicio, fim, esperado):
    assert meses_entre(inicio, fim) == esperado
