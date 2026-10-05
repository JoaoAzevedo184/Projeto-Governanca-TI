"""Scorecard de fornecedores (FR-011, BR-029): funções puras, esperado calculado à mão."""

from decimal import Decimal as D

import pytest

from app.utils.scorecard import pesos_somam_100, pontuacao, ranking, soma_dos_pesos


@pytest.mark.parametrize(
    ("pesos", "soma", "ok"),
    [
        ([D("30"), D("30"), D("40")], D("100"), True),
        ([D("50"), D("25"), D("25")], D("100"), True),
        ([D("10.10"), D("20.20"), D("69.70")], D("100.00"), True),
        ([D("30"), D("30"), D("35")], D("95"), False),  # AC-048
        ([D("30"), D("30"), D("40.01")], D("100.01"), False),
        ([D("33.33"), D("33.33"), D("33.33")], D("99.99"), False),
        ([D("0.1"), D("0.2"), D("99.7")], D("100.0"), True),
    ],
)
def test_br029_pesos_precisam_somar_exatamente_100(pesos, soma, ok):
    assert soma_dos_pesos(pesos) == soma
    assert pesos_somam_100(pesos) is ok


def test_soma_de_pesos_usa_decimal_e_nao_cai_na_armadilha_do_float():
    assert 0.1 + 0.2 != 0.3  # o motivo da regra: o float binário erra a soma
    assert pesos_somam_100([D("0.1"), D("0.2"), D("99.7")]) is True  # Decimal fecha 100 exato
    assert pesos_somam_100([D("0.3"), D("0.3"), D("0.4")]) is False  # soma 1,0, não 100


def test_pontuacao_e_a_soma_ponderada_das_notas():
    pesos = {"preco": D("40"), "prazo": D("30"), "suporte": D("30")}

    # 8×0,40 + 6×0,30 + 9×0,30 = 3,20 + 1,80 + 2,70
    assert pontuacao({"preco": D("8"), "prazo": D("6"), "suporte": D("9")}, pesos) == D("7.70")
    assert pontuacao({"preco": D("10"), "prazo": D("10"), "suporte": D("10")}, pesos) == D("10.00")
    assert pontuacao({"preco": D("0"), "prazo": D("0"), "suporte": D("0")}, pesos) == D("0.00")


def test_pontuacao_arredonda_so_no_fim_e_meio_centavo_sobe():
    metade = {"a": D("50"), "b": D("50")}

    # 0,25×0,50 + 0×0,50 = 0,125 → 0,13 (half-up; half-even daria 0,12)
    assert pontuacao({"a": D("0.25"), "b": D("0")}, metade) == D("0.13")
    # 7,00×0,3333 + 8,00×0,3333 + 9,00×0,3334 = 2,3331 + 2,6664 + 3,0006 = 8,0001
    terços = {"a": D("33.33"), "b": D("33.33"), "c": D("33.34")}
    assert pontuacao({"a": D("7"), "b": D("8"), "c": D("9")}, terços) == D("8.00")


def test_ranking_ordena_do_maior_para_o_menor():
    resultado = ranking({1: D("7.20"), 2: D("8.10"), 3: D("5.00")})

    assert resultado == [(1, 2, D("8.10")), (2, 1, D("7.20")), (3, 3, D("5.00"))]


def test_ranking_desempata_pelo_menor_id_com_posicoes_sequenciais():
    resultado = ranking({7: D("7.20"), 3: D("7.20"), 5: D("9.00")})

    assert resultado == [(1, 5, D("9.00")), (2, 3, D("7.20")), (3, 7, D("7.20"))]


def test_ranking_vazio():
    assert ranking({}) == []
