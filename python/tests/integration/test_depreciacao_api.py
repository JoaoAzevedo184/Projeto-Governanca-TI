"""Depreciação exposta pela API (FR-003): rota dedicada e bloco no ativo."""

from datetime import date
from decimal import Decimal

import pytest

from app.models.ativo import Ativo
from app.services import depreciacao_service

CAMPOS_CONTRATO = {
    "ativo_id",
    "data_referencia",
    "metodo",
    "valor_compra",
    "vida_util_meses",
    "meses_decorridos",
    "meses_efetivos",
    "depreciacao_mensal",
    "depreciacao_acumulada",
    "valor_residual",
    "percentual_depreciado",
}


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _criar_ativo(client, token, categoria, fornecedor, **sobrescritas):
    payload = {
        "nome": "Notebook Depreciacao",
        "tipo": "HARDWARE",
        "categoria_id": categoria.id,
        "fornecedor_id": fornecedor.id,
        "numero_serie": "SN-DEP",
        "data_aquisicao": "2025-03-14",
        "valor_compra": 6000.00,
        **sobrescritas,
    }
    resposta = client.post("/api/v1/ativos", headers=_headers(token), json=payload)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_ac018_ativo_recem_cadastrado_ja_traz_depreciacao_calculada(
    client, token_admin, categoria, fornecedor
):
    criado = _criar_ativo(client, token_admin, categoria, fornecedor)

    assert set(criado["depreciacao"]) == CAMPOS_CONTRATO
    assert criado["depreciacao"]["ativo_id"] == criado["id"]
    assert criado["depreciacao"]["metodo"] == "LINEAR"
    assert criado["depreciacao"]["data_referencia"] == date.today().isoformat()

    detalhe = client.get(f"/api/v1/ativos/{criado['id']}", headers=_headers(token_admin)).json()
    listagem = client.get("/api/v1/ativos", headers=_headers(token_admin)).json()
    atualizado = client.patch(
        f"/api/v1/ativos/{criado['id']}", headers=_headers(token_admin), json={"localizacao": "A"}
    ).json()
    for corpo in (detalhe, listagem["itens"][0], atualizado):
        assert corpo["depreciacao"] == criado["depreciacao"]


def test_get_depreciacao_segue_o_contrato(
    client, token_auditor, token_admin, categoria, fornecedor
):
    criado = _criar_ativo(client, token_admin, categoria, fornecedor)

    resposta = client.get(
        f"/api/v1/ativos/{criado['id']}/depreciacao", headers=_headers(token_auditor)
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert set(corpo) == CAMPOS_CONTRATO
    assert corpo == criado["depreciacao"]
    assert Decimal(corpo["valor_compra"]) == Decimal("6000.00")
    assert corpo["vida_util_meses"] == 60
    assert Decimal(corpo["depreciacao_mensal"]) == Decimal("100.00")


def test_get_depreciacao_de_ativo_inexistente_retorna_404(client, token_admin):
    resposta = client.get("/api/v1/ativos/999/depreciacao", headers=_headers(token_admin))
    assert resposta.status_code == 404
    assert resposta.json()["regra"] is None


def test_ac015_servico_calcula_na_data_de_referencia_injetada(
    client, db, token_admin, categoria, fornecedor
):
    criado = _criar_ativo(client, token_admin, categoria, fornecedor)

    resultado = depreciacao_service.calcular_para_ativo(
        db.get(Ativo, criado["id"]), date(2026, 3, 14)
    )

    assert resultado.data_referencia == date(2026, 3, 14)
    assert resultado.depreciacao_acumulada == Decimal("1200.00")
    assert resultado.valor_residual == Decimal("4800.00")
    assert resultado.percentual_depreciado == Decimal("20.00")


def test_ac020_categorias_com_vidas_uteis_distintas_depreciam_diferente(
    client, db, token_admin, categoria, fornecedor
):
    smartphone = client.post(
        "/api/v1/categorias",
        headers=_headers(token_admin),
        json={"nome": "Smartphone", "vida_util_meses": 36, "tipo_aplicavel": "HARDWARE"},
    ).json()
    notebook = _criar_ativo(client, token_admin, categoria, fornecedor, numero_serie="SN-60")
    celular = _criar_ativo(
        client,
        token_admin,
        categoria,
        fornecedor,
        numero_serie="SN-36",
        categoria_id=smartphone["id"],
    )
    referencia = date(2026, 3, 14)

    sessenta, trinta_e_seis = (
        depreciacao_service.calcular_para_ativo(db.get(Ativo, a["id"]), referencia)
        for a in (notebook, celular)
    )

    assert sessenta.depreciacao_acumulada == Decimal("1200.00")
    assert trinta_e_seis.depreciacao_acumulada == Decimal("2000.00")  # 6.000,00 × 12 ÷ 36


def test_br006_vida_util_herdada_nao_muda_quando_a_categoria_muda(
    client, token_admin, categoria, fornecedor
):
    criado = _criar_ativo(client, token_admin, categoria, fornecedor)

    alterada = client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=_headers(token_admin),
        json={"vida_util_meses": 24},
    )
    assert alterada.status_code == 200
    depois = client.get(
        f"/api/v1/ativos/{criado['id']}/depreciacao", headers=_headers(token_admin)
    ).json()

    assert depois["vida_util_meses"] == 60
    assert depois == criado["depreciacao"]


def test_vida_util_sobrescrita_no_ativo_prevalece_sobre_a_categoria(
    client, token_admin, categoria, fornecedor
):
    criado = _criar_ativo(client, token_admin, categoria, fornecedor, vida_util_meses=12)

    assert criado["depreciacao"]["vida_util_meses"] == 12
    assert Decimal(criado["depreciacao"]["depreciacao_mensal"]) == Decimal("500.00")


@pytest.mark.parametrize("tipo", ["HARDWARE", "SOFTWARE"])
def test_software_deprecia_pela_mesma_regra_linear_da_categoria(
    client, db, token_admin, fornecedor, tipo
):
    # ADR-012: software é ativo; FR-003 trata "Software (licença perpétua)" como 60 meses linear.
    categoria = client.post(
        "/api/v1/categorias",
        headers=_headers(token_admin),
        json={"nome": f"Categoria {tipo}", "vida_util_meses": 60, "tipo_aplicavel": tipo},
    ).json()
    identificador = {"numero_serie": "SN-T"} if tipo == "HARDWARE" else {"chave_licenca": "K-T"}
    payload = {
        "nome": f"Ativo {tipo}",
        "tipo": tipo,
        "categoria_id": categoria["id"],
        "fornecedor_id": fornecedor.id,
        "data_aquisicao": "2025-03-14",
        "valor_compra": 6000.00,
        **identificador,
    }
    criado = client.post("/api/v1/ativos", headers=_headers(token_admin), json=payload).json()

    resultado = depreciacao_service.calcular_para_ativo(
        db.get(Ativo, criado["id"]), date(2026, 3, 14)
    )

    assert resultado.valor_residual == Decimal("4800.00")
