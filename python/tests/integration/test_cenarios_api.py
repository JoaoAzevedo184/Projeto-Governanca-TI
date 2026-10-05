"""Cenários e TCO (FR-010): AC-052 e BR-028. Dinheiro como string; esperado calculado à mão.

Cenário-base (400 ativos no parque), contrato §6.7:
MANTER   capex 0       opex 84.000 → TCO 420.000,00 · 210,00/ativo/ano · riscos 16
RENOVAR  capex 300.000 opex 20.000 → TCO 400.000,00 · 200,00/ativo/ano · riscos 6
MIGRAR   capex 50.000  opex 70.000 → TCO 400.000,00 · 200,00/ativo/ano · riscos 4
"""

import pytest
from sqlalchemy import func, select

from app.models.auditoria import AuditLog
from app.models.risco import Risco


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _risco(client, token, probabilidade, impacto, titulo="Risco de teste"):
    resposta = client.post(
        "/api/v1/riscos",
        headers=_headers(token),
        json={
            "titulo": titulo,
            "categoria": "FINANCEIRO",
            "probabilidade": probabilidade,
            "impacto": impacto,
            "resposta": "MITIGAR",
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


@pytest.fixture
def corpo(client, token_admin):
    r16 = _risco(client, token_admin, 4, 4, "Risco 16")
    r6a = _risco(client, token_admin, 2, 3, "Risco 6")
    r4 = _risco(client, token_admin, 1, 4, "Risco 4")
    return {
        "quantidade_ativos": 400,
        "cenarios": [
            {"nome": "MANTER", "capex": "0", "opex_anual": "84000", "riscos_ids": [r16]},
            {"nome": "RENOVAR", "capex": "300000", "opex_anual": "20000", "riscos_ids": [r6a]},
            {
                "nome": "MIGRAR_ASSINATURA",
                "capex": "50000",
                "opex_anual": "70000",
                "riscos_ids": [r4],
            },
        ],
    }


def _comparar(client, token, corpo):
    return client.post("/api/v1/cenarios/comparar", headers=_headers(token), json=corpo)


def test_ac052_cenarios_ordenados_por_custo_e_risco_e_nenhum_escolhido(client, token_admin, corpo):
    resposta = _comparar(client, token_admin, corpo)

    assert resposta.status_code == 200, resposta.text
    saida = resposta.json()
    assert saida["horizonte_anos"] == 5
    assert saida["ordenado_por"] == ["tco_5_anos", "score_risco"]
    # TCO empatado em 400.000: o de menor score de risco (4) vem antes do de 6.
    assert [c["nome"] for c in saida["cenarios"]] == ["MIGRAR_ASSINATURA", "RENOVAR", "MANTER"]
    assert [c["tco_5_anos"] for c in saida["cenarios"]] == ["400000.00", "400000.00", "420000.00"]
    assert [c["score_risco"] for c in saida["cenarios"]] == [4, 6, 16]
    # BR-028: ordena, não escolhe. Nenhum campo ou valor de seleção em lugar nenhum da resposta.
    texto = resposta.text.lower()
    assert "escolhid" not in texto and "selecionad" not in texto and "vencedor" not in texto
    for cenario in saida["cenarios"]:
        assert set(cenario) == {
            "nome",
            "capex",
            "opex_anual",
            "tco_5_anos",
            "custo_por_ativo_ano",
            "economia_vs_baseline",
            "score_risco",
        }
    assert "decisão humana" in saida["observacao"] and "/recomendacoes" in saida["observacao"]


def test_valores_do_contrato_dinheiro_como_string(client, token_admin, corpo):
    saida = _comparar(client, token_admin, corpo).json()

    por_nome = {c["nome"]: c for c in saida["cenarios"]}
    manter = por_nome["MANTER"]
    assert (manter["capex"], manter["opex_anual"]) == ("0.00", "84000.00")
    assert manter["tco_5_anos"] == "420000.00"  # 0 + 5 × 84.000
    assert manter["custo_por_ativo_ano"] == "210.00"  # 420.000 ÷ (400 × 5)
    assert manter["economia_vs_baseline"] == "0.00"
    renovar = por_nome["RENOVAR"]
    assert renovar["tco_5_anos"] == "400000.00" and renovar["custo_por_ativo_ano"] == "200.00"
    assert renovar["economia_vs_baseline"] == "20000.00"  # 420.000 − 400.000
    assert saida["baseline"] == "MANTER" and saida["quantidade_ativos"] == 400


def test_comparacao_nao_persiste_nada_nem_audita(client, db, token_admin, corpo):
    riscos = db.scalar(select(func.count()).select_from(Risco))
    auditoria = db.scalar(select(func.count()).select_from(AuditLog))

    _comparar(client, token_admin, corpo)

    assert db.scalar(select(func.count()).select_from(Risco)) == riscos
    assert db.scalar(select(func.count()).select_from(AuditLog)) == auditoria  # só calcula


def test_score_de_risco_soma_os_riscos_do_cenario(client, token_admin, corpo):
    extra = _risco(client, token_admin, 5, 5, "Risco 25")
    corpo["cenarios"][0]["riscos_ids"].append(extra)

    saida = _comparar(client, token_admin, corpo).json()

    assert {c["nome"]: c["score_risco"] for c in saida["cenarios"]}["MANTER"] == 41  # 16 + 25


def test_cenario_sem_riscos_tem_score_zero(client, token_admin, corpo):
    corpo["cenarios"][1]["riscos_ids"] = []

    saida = _comparar(client, token_admin, corpo).json()

    assert {c["nome"]: c["score_risco"] for c in saida["cenarios"]}["RENOVAR"] == 0


def test_dois_cenarios_sem_manter_usam_o_primeiro_como_baseline(client, token_admin, corpo):
    corpo["cenarios"] = corpo["cenarios"][1:]  # RENOVAR e MIGRAR

    saida = _comparar(client, token_admin, corpo).json()

    assert saida["baseline"] == "RENOVAR"
    assert {c["nome"]: c["economia_vs_baseline"] for c in saida["cenarios"]} == {
        "RENOVAR": "0.00",
        "MIGRAR_ASSINATURA": "0.00",
    }


def test_quantidade_de_ativos_padrao_e_a_dos_ativos_nao_baixados(
    client, token_admin, novo_ativo, corpo
):
    corpo.pop("quantidade_ativos")
    for _ in range(3):
        novo_ativo()
    baixado = novo_ativo()
    client.post(
        f"/api/v1/ativos/{baixado}/baixa",
        headers=_headers(token_admin),
        json={"motivo": "DEFEITO", "data_baixa": "2025-07-10", "destinacao": "DESCARTE"},
    )

    saida = _comparar(client, token_admin, corpo).json()

    assert saida["quantidade_ativos"] == 3  # o baixado não conta
    assert {c["nome"]: c["custo_por_ativo_ano"] for c in saida["cenarios"]}["MANTER"] == "28000.00"
    # 420.000 ÷ (3 × 5) = 28.000,00


def test_sem_ativos_o_custo_por_ativo_e_nulo(client, token_admin, corpo):
    corpo.pop("quantidade_ativos")

    saida = _comparar(client, token_admin, corpo).json()

    assert saida["quantidade_ativos"] == 0
    assert {c["custo_por_ativo_ano"] for c in saida["cenarios"]} == {None}


def test_risco_inexistente_e_404(client, token_admin, corpo):
    corpo["cenarios"][0]["riscos_ids"] = [9999]

    resposta = _comparar(client, token_admin, corpo)

    assert resposta.status_code == 404


@pytest.mark.parametrize(
    "ajuste",
    [
        lambda c: c.update(cenarios=c["cenarios"][:1]),  # um só
        lambda c: c["cenarios"].append({"nome": "MANTER", "capex": "1", "opex_anual": "1"}),  # 4
        lambda c: c["cenarios"][1].update(nome="MANTER"),  # repetido
        lambda c: c["cenarios"][0].update(nome="OUTRO"),
        lambda c: c["cenarios"][0].update(capex="-1"),
        lambda c: c["cenarios"][0].update(opex_anual="-0.01"),
        lambda c: c["cenarios"][0].update(capex="1.234"),
        lambda c: c["cenarios"][0].update(capex="muito"),
        lambda c: c.update(quantidade_ativos=0),
        lambda c: c["cenarios"][0].update(riscos_ids=[1, 1]),
        lambda c: c["cenarios"][0].pop("opex_anual"),
        lambda c: c.pop("cenarios"),
    ],
)
def test_corpo_invalido_e_422(client, token_admin, corpo, ajuste):
    ajuste(corpo)

    assert _comparar(client, token_admin, corpo).status_code == 422


def test_gestor_compara_e_operador_e_auditor_recebem_403(
    client, token_gestor, token_operador, token_auditor, corpo
):
    assert _comparar(client, token_gestor, corpo).status_code == 200
    assert _comparar(client, token_operador, corpo).status_code == 403
    assert _comparar(client, token_auditor, corpo).status_code == 403
