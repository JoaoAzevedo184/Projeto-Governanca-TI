"""Score e classificação de risco (FR-012, AC-050): função pura, esperado escrito à mão."""

import pytest

from app.models.enums import ClassificacaoRisco as C
from app.utils.risco import FAIXAS, calcular_score, classificar


@pytest.mark.parametrize(
    ("probabilidade", "impacto", "esperado"),
    [(1, 1, 1), (4, 5, 20), (5, 5, 25), (2, 3, 6), (3, 3, 9), (5, 1, 5)],
)
def test_score_e_probabilidade_vezes_impacto(probabilidade, impacto, esperado):
    assert calcular_score(probabilidade, impacto) == esperado


@pytest.mark.parametrize(
    ("score", "esperado"),
    [
        (1, C.BAIXO),
        (4, C.BAIXO),
        (5, C.MEDIO),
        (9, C.MEDIO),
        (10, C.ALTO),
        (14, C.ALTO),
        (15, C.CRITICO),
        (20, C.CRITICO),
        (25, C.CRITICO),
    ],
)
def test_classificacao_pelas_faixas_do_prd_com_limites_inclusivos(score, esperado):
    assert classificar(score) == esperado


@pytest.mark.parametrize("score", [0, -1, 26])
def test_score_fora_de_1_a_25_nao_classifica(score):
    with pytest.raises(ValueError, match="fora de 1 a 25"):
        classificar(score)


def test_faixas_cobrem_1_a_25_sem_buracos_nem_sobreposicao():
    cobertos = [s for minimo, maximo in FAIXAS.values() for s in range(minimo, maximo + 1)]

    assert sorted(cobertos) == list(range(1, 26))


def test_todo_produto_possivel_cai_em_alguma_faixa():
    for p in range(1, 6):
        for i in range(1, 6):
            assert classificar(calcular_score(p, i)) in C
