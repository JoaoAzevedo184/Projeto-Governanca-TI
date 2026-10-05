"""TCO de cenários (FR-010, BR-028): funções puras, esperado calculado à mão."""

from dataclasses import fields
from decimal import Decimal as D

import pytest

from app.utils.cenario import (
    EntradaCenario,
    ResultadoCenario,
    comparar,
    custo_por_ativo_ano,
    escolher_baseline,
    tco,
)


def test_tco_de_5_anos_e_capex_mais_opex_vezes_5():
    assert tco(D("0"), D("84000")) == D("420000.00")  # exemplo do contrato §6.7
    assert tco(D("300000"), D("20000")) == D("400000.00")  # 300.000 + 5 × 20.000
    assert tco(D("1000.10"), D("200.05")) == D("2000.35")  # 1.000,10 + 5 × 200,05
    assert tco(D("0"), D("0")) == D("0.00")


def test_custo_por_ativo_ano_e_tco_sobre_ativos_vezes_5():
    assert custo_por_ativo_ano(D("420000.00"), 400) == D("210.00")  # 420.000 ÷ (400 × 5)
    assert custo_por_ativo_ano(D("100.00"), 3) == D("6.67")  # 100 ÷ 15 = 6,6666…
    assert custo_por_ativo_ano(D("1.00"), 8) == D("0.03")  # 1 ÷ 40 = 0,025 → half-up
    assert custo_por_ativo_ano(D("0.00"), 10) == D("0.00")


@pytest.mark.parametrize("ativos", [0, -1])
def test_sem_ativos_nao_ha_custo_por_ativo(ativos):
    assert custo_por_ativo_ano(D("1000"), ativos) is None


def test_baseline_e_o_manter_quando_presente_senao_o_primeiro():
    assert escolher_baseline(["RENOVAR", "MANTER", "MIGRAR_ASSINATURA"]) == "MANTER"
    assert escolher_baseline(["RENOVAR", "MIGRAR_ASSINATURA"]) == "RENOVAR"


def _entradas():
    return [
        EntradaCenario("MANTER", D("0"), D("84000"), 16),
        EntradaCenario("RENOVAR", D("300000"), D("20000"), 6),
        EntradaCenario("MIGRAR_ASSINATURA", D("50000"), D("70000"), 4),
    ]


def test_comparar_ordena_por_tco_depois_por_score_de_risco():
    resultado = comparar(_entradas(), 400, "MANTER")

    # TCOs: MANTER 420.000; RENOVAR 400.000; MIGRAR 400.000 (empate, desempata o menor score: 4 < 6)
    assert [r.nome for r in resultado] == ["MIGRAR_ASSINATURA", "RENOVAR", "MANTER"]
    assert [r.tco_5_anos for r in resultado] == [D("400000.00"), D("400000.00"), D("420000.00")]
    assert [r.score_risco for r in resultado] == [4, 6, 16]


def test_comparar_calcula_economia_contra_o_baseline_e_custo_por_ativo():
    por_nome = {r.nome: r for r in comparar(_entradas(), 400, "MANTER")}

    assert por_nome["MANTER"].economia_vs_baseline == D("0.00")
    assert por_nome["RENOVAR"].economia_vs_baseline == D("20000.00")  # 420.000 − 400.000
    assert por_nome["MANTER"].custo_por_ativo_ano == D("210.00")
    assert por_nome["RENOVAR"].custo_por_ativo_ano == D("200.00")  # 400.000 ÷ 2.000


def test_economia_negativa_quando_o_cenario_custa_mais_que_o_baseline():
    resultado = comparar(
        [
            EntradaCenario("MANTER", D("0"), D("10"), 1),
            EntradaCenario("RENOVAR", D("500"), D("10"), 1),
        ],
        1,
        "MANTER",
    )

    assert {r.nome: r.economia_vs_baseline for r in resultado} == {
        "MANTER": D("0.00"),
        "RENOVAR": D("-500.00"),  # custa 500 a mais
    }


def test_empate_total_desempata_pelo_nome_e_baseline_pode_ser_outro():
    resultado = comparar(
        [
            EntradaCenario("RENOVAR", D("0"), D("10"), 5),
            EntradaCenario("MIGRAR_ASSINATURA", D("0"), D("10"), 5),
        ],
        10,
        "RENOVAR",
    )

    assert [r.nome for r in resultado] == ["MIGRAR_ASSINATURA", "RENOVAR"]
    assert {r.economia_vs_baseline for r in resultado} == {D("0.00")}


def test_br028_o_resultado_nao_tem_campo_de_escolha():
    campos = {f.name for f in fields(ResultadoCenario)}

    assert campos == {
        "nome",
        "capex",
        "opex_anual",
        "tco_5_anos",
        "custo_por_ativo_ano",
        "economia_vs_baseline",
        "score_risco",
    }
