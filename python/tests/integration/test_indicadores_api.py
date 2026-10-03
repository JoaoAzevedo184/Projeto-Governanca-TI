"""Indicadores de ITAM (FR-009): AC-047. Esperado calculado à mão, com data de referência fixa.

Cenário (referência 2026-03-20, categoria de 60 meses de vida útil; depreciação linear):

| ativo | tipo     | valor    | aquisição  | meses | residual | status        | responsável |
|-------|----------|----------|------------|-------|----------|---------------|-------------|
| A     | HARDWARE | 6.000,00 | 2025-03-20 | 12    | 4.800,00 | ATIVO         | sim (2025-04-01) |
| B     | HARDWARE | 3.000,00 | 2024-03-20 | 24    | 1.800,00 | ATIVO         | não         |
| C     | SOFTWARE | 1.200,00 | 2026-01-20 | 2     | 1.160,00 | EM_MANUTENCAO | não         |
| D     | HARDWARE | 2.000,00 | 2025-01-10 | —     | congelado| BAIXADO (2025-07-10) | — |

Licenças: L1 em dia, L2 vencida em 2026-03-01 (CP-01), L3 vence em 2026-04-01 (CP-03, conforme).
"""

from datetime import date
from decimal import Decimal

import pytest

from app.models.ativo import Ativo
from app.services import indicador_service

REF = date(2026, 3, 20)


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def parque(client, db, token_admin, novo_ativo, nova_licenca, responsavel, setor):
    a = novo_ativo(valor="6000.00", data_aquisicao="2025-03-20")
    b = novo_ativo(valor="3000.00", data_aquisicao="2024-03-20")
    c = novo_ativo(tipo="SOFTWARE", valor="1200.00", data_aquisicao="2026-01-20")
    d = novo_ativo(valor="2000.00", data_aquisicao="2025-01-10")
    atribuicao = client.post(
        f"/api/v1/ativos/{a}/responsavel",
        headers=_headers(token_admin),
        json={"responsavel_id": responsavel.id, "setor_id": setor.id, "data_inicio": "2025-04-01"},
    )
    assert atribuicao.status_code == 201, atribuicao.text
    baixa = client.post(
        f"/api/v1/ativos/{d}/baixa",
        headers=_headers(token_admin),
        json={"motivo": "DEFEITO", "data_baixa": "2025-07-10", "destinacao": "DESCARTE"},
    )
    assert baixa.status_code == 201, baixa.text
    db.query(Ativo).filter(Ativo.id == c).update({"status": "EM_MANUTENCAO"})
    db.commit()
    nova_licenca()  # L1
    nova_licenca(expiracao="2026-03-01")  # L2
    nova_licenca(expiracao="2026-04-01")  # L3
    return {"a": a, "b": b, "c": c, "d": d}


def _por_codigo(resposta):
    return {i.codigo: i for i in resposta.indicadores}


def test_indicadores_do_parque_conferem_com_a_conta_a_mao(db, parque):
    resposta = indicador_service.calcular_indicadores(db, data_referencia=REF)

    i = _por_codigo(resposta)
    assert (i["IND-01"].valor, i["IND-01"].detalhe) == (
        4,
        {"ATIVO": 2, "EM_MANUTENCAO": 1, "BAIXADO": 1},
    )
    assert i["IND-02"].detalhe == {"HARDWARE": 3, "SOFTWARE": 1}
    assert i["IND-03"].valor == "10200.00"  # 6.000 + 3.000 + 1.200, sem o baixado
    assert i["IND-04"].valor == "7760.00"  # 4.800 + 1.800 + 1.160, sem o baixado
    assert i["IND-05"].valor == 23.92  # (1 − 7.760 / 10.200) × 100
    assert i["IND-06"].valor == "3400.00"  # 10.200 / 3 ativos não baixados
    assert i["KPI-02"].valor == 50.0  # só A, de A e B (status ATIVO), tem responsável
    assert i["KPI-03"].valor == 66.67  # L1 e L3 conformes, L2 vencida: 2 / 3
    assert i["KPI-06"].valor == 33.33  # só B sem evento nos últimos 12 meses: 1 / 3
    assert i["KPI-07"].valor == 12.67  # (12 + 24 + 2) / 3 meses
    assert i["IND-07"].valor == 33.33  # 1 baixa / 3 ativos existentes em 2025-03-20 (A, B, D)
    assert i["KPI-08"].valor == 100.0  # a baixa de D tem destinação


def test_ac047_cada_indicador_traz_formula_e_tamanho_da_amostra(db, parque):
    resposta = indicador_service.calcular_indicadores(db, data_referencia=REF)

    i = _por_codigo(resposta)
    assert all(ind.formula for ind in resposta.indicadores)
    assert {
        k: i[k].amostra for k in ("IND-01", "IND-03", "KPI-02", "KPI-03", "KPI-06", "IND-07")
    } == {
        "IND-01": 4,
        "IND-03": 3,
        "KPI-02": 2,
        "KPI-03": 3,
        "KPI-06": 3,
        "IND-07": 3,
    }
    assert i["KPI-02"].formula == "ativos com vínculo aberto / ativos com status ATIVO * 100"


def test_ac047_endpoint_expoe_formula_amostra_e_filtros(client, token_admin, parque):
    resposta = client.get("/api/v1/indicadores", headers=_headers(token_admin))

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert set(corpo["filtros_aplicados"]) == {
        "categoria_id",
        "setor_id",
        "fornecedor_id",
        "data_inicio",
        "data_fim",
    }
    for indicador in corpo["indicadores"]:
        assert indicador["formula"]
        assert isinstance(indicador["amostra"], int)
    por_codigo = {x["codigo"]: x for x in corpo["indicadores"]}
    assert isinstance(por_codigo["IND-03"]["valor"], str)  # valor monetário como string
    assert por_codigo["KPI-02"]["meta"] == 98.0


def test_metas_dos_kpis_e_se_atendem(db, parque):
    i = _por_codigo(indicador_service.calcular_indicadores(db, data_referencia=REF))

    assert (i["KPI-02"].meta, i["KPI-02"].atende_meta) == (98, False)  # 50 < 98
    assert (i["KPI-03"].meta, i["KPI-03"].atende_meta) == (100, False)
    assert (i["KPI-06"].sentido_meta, i["KPI-06"].atende_meta) == ("<=", False)  # 33,33 > 10
    assert i["KPI-08"].atende_meta is True
    assert i["KPI-07"].meta is None and i["KPI-07"].atende_meta is None


def test_filtro_por_setor_considera_o_setor_do_vinculo_aberto(db, parque, setor):
    resposta = indicador_service.calcular_indicadores(db, setor_id=setor.id, data_referencia=REF)

    i = _por_codigo(resposta)
    assert i["IND-01"].valor == 1  # só A está no setor
    assert i["IND-03"].valor == "6000.00"
    assert i["KPI-02"].valor == 100.0
    assert resposta.filtros_aplicados["setor_id"] == setor.id


def test_filtro_por_categoria_e_fornecedor_sem_resultado_deixa_o_valor_nulo(db, parque):
    resposta = indicador_service.calcular_indicadores(
        db, categoria_id=9999, fornecedor_id=9999, data_referencia=REF
    )

    i = _por_codigo(resposta)
    assert i["IND-01"].valor == 0 and i["IND-01"].amostra == 0
    assert i["IND-03"].valor == "0.00"
    for codigo in ("IND-05", "IND-06", "KPI-02", "KPI-03", "KPI-06", "KPI-07", "IND-07", "KPI-08"):
        assert i[codigo].valor is None, codigo
        assert i[codigo].atende_meta is None


def test_periodo_define_a_taxa_de_baixas(db, parque):
    fora = indicador_service.calcular_indicadores(
        db, data_inicio=date(2025, 8, 1), data_fim=REF, data_referencia=REF
    )
    dentro = indicador_service.calcular_indicadores(
        db, data_inicio=date(2025, 1, 1), data_fim=date(2025, 12, 31), data_referencia=REF
    )

    # Em 2025-08-01 existem A, B (D já foi baixado em 2025-07-10): 0 baixas / 2.
    assert _por_codigo(fora)["IND-07"].valor == 0.0
    assert _por_codigo(fora)["IND-07"].amostra == 2
    # Em 2025-01-01 só B existe (A e D são de 2025-03-20 e 2025-01-10): 1 baixa / 1.
    assert _por_codigo(dentro)["IND-07"].valor == 100.0
    assert _por_codigo(dentro)["IND-07"].amostra == 1


def test_licenca_a_vencer_conta_como_conforme_no_kpi03(db, nova_licenca):
    nova_licenca(expiracao="2026-03-25")  # CP-03: alerta, mas ainda conforme (KPI-03)

    kpi = _por_codigo(indicador_service.calcular_indicadores(db, data_referencia=REF))["KPI-03"]

    assert kpi.valor == 100.0 and kpi.atende_meta is True


def test_vinculo_encerrado_pela_baixa_nao_conta_como_ativo_ocioso_nem_patrimonio(
    client, db, token_admin, novo_ativo, responsavel, setor
):
    ativo = novo_ativo(valor="6000.00", data_aquisicao="2025-03-20")
    client.post(
        f"/api/v1/ativos/{ativo}/responsavel",
        headers=_headers(token_admin),
        json={"responsavel_id": responsavel.id, "setor_id": setor.id, "data_inicio": "2025-04-01"},
    )
    client.post(
        f"/api/v1/ativos/{ativo}/baixa",
        headers=_headers(token_admin),
        json={"motivo": "DEFEITO", "data_baixa": "2025-07-10", "destinacao": "DESCARTE"},
    )

    i = _por_codigo(indicador_service.calcular_indicadores(db, data_referencia=REF))

    assert i["IND-03"].valor == "0.00"
    assert i["IND-03"].amostra == 0
    assert i["KPI-02"].valor is None  # nenhum ativo com status ATIVO
    assert Decimal(i["IND-04"].valor) == Decimal("0.00")
