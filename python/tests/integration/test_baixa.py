"""Baixa de ativo (FR-005): AC-011, AC-019, AC-027 a AC-030, AC-032 e AC-033."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models.ativo import Ativo
from app.models.auditoria import AuditLog
from app.models.baixa import BaixaAtivo
from app.models.enums import StatusAtivo
from app.models.historico import HistoricoTransferencia
from app.models.responsavel import Responsavel
from app.utils import datas

AQUISICAO = "2025-01-10"
BAIXA = {
    "motivo": "DEFEITO",
    "justificativa": "Placa-mãe queimada, reparo inviável",
    "data_baixa": "2025-07-10",
    "destinacao": "RECICLAGEM_CERTIFICADA",
}


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def outros_responsaveis(db, setor):
    registros = [
        Responsavel(nome=f"Colaborador {n}", matricula=f"M-20{n}", setor_id=setor.id)
        for n in range(2)
    ]
    db.add_all(registros)
    db.commit()
    return registros


@pytest.fixture
def ativo_id(client, token_admin, categoria, fornecedor):
    payload = {
        "nome": "Notebook Baixa",
        "tipo": "HARDWARE",
        "categoria_id": categoria.id,
        "fornecedor_id": fornecedor.id,
        "numero_serie": "SN-BAIXA",
        "data_aquisicao": AQUISICAO,
        "valor_compra": "6000.00",
    }
    resposta = client.post("/api/v1/ativos", headers=_headers(token_admin), json=payload)
    assert resposta.status_code == 201
    return resposta.json()["id"]


def _baixar(client, token, ativo_id, **sobrescritas):
    corpo = {**BAIXA, **sobrescritas}
    corpo = {chave: valor for chave, valor in corpo.items() if valor is not ...}
    return client.post(f"/api/v1/ativos/{ativo_id}/baixa", headers=_headers(token), json=corpo)


def _vincular(client, token, ativo_id, responsavel, setor, data_inicio):
    corpo = {"responsavel_id": responsavel.id, "setor_id": setor.id, "data_inicio": data_inicio}
    resposta = client.post(
        f"/api/v1/ativos/{ativo_id}/responsavel", headers=_headers(token), json=corpo
    )
    assert resposta.status_code == 201
    return resposta.json()


def _total(db, modelo) -> int:
    return db.scalar(select(func.count()).select_from(modelo))


def _recusas(db):
    return [
        (a.entidade, a.operacao, a.regra_violada)
        for a in db.scalars(select(AuditLog).where(AuditLog.resultado == "RECUSADO"))
    ]


def _assert_recusada(resposta, db, ativo_id, regra):
    assert resposta.status_code == 409, resposta.text
    assert resposta.json()["regra"] == regra
    assert _total(db, BaixaAtivo) == 0
    db.expire_all()
    assert db.get(Ativo, ativo_id).status == StatusAtivo.ATIVO
    assert _recusas(db) == [("baixa_ativo", "CRIAR", regra)]


def test_ac027_baixa_marca_baixado_e_encerra_o_vinculo_aberto(
    client, db, token_admin, ativo_id, responsavel, setor
):
    _vincular(client, token_admin, ativo_id, responsavel, setor, "2025-02-01")

    resposta = _baixar(client, token_admin, ativo_id)

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["ativo_id"] == ativo_id
    assert corpo["motivo"] == "DEFEITO"
    assert corpo["destinacao"] == "RECICLAGEM_CERTIFICADA"
    assert corpo["data_source"] == "manual"
    db.expire_all()
    assert db.get(Ativo, ativo_id).status == StatusAtivo.BAIXADO
    vinculo = db.scalars(select(HistoricoTransferencia)).one()
    assert vinculo.data_fim == date(2025, 7, 10)  # BR-012: data_fim = data da baixa


def test_baixa_de_ativo_sem_responsavel_nao_exige_vinculo(client, db, token_admin, ativo_id):
    resposta = _baixar(client, token_admin, ativo_id)

    assert resposta.status_code == 201
    assert _total(db, HistoricoTransferencia) == 0


def test_ac028_motivo_outro_sem_justificativa_e_recusado(client, db, token_admin, ativo_id):
    resposta = _baixar(client, token_admin, ativo_id, motivo="OUTRO", justificativa=...)

    _assert_recusada(resposta, db, ativo_id, "BR-023")


@pytest.mark.parametrize("justificativa", ["", "   ", "curta", "  nove car  "])
def test_ac028_justificativa_vazia_ou_menor_que_10_e_recusada(
    client, db, token_admin, ativo_id, justificativa
):
    resposta = _baixar(client, token_admin, ativo_id, motivo="OUTRO", justificativa=justificativa)

    _assert_recusada(resposta, db, ativo_id, "BR-023")


def test_motivo_outro_com_justificativa_de_10_caracteres_e_aceito(client, token_admin, ativo_id):
    resposta = _baixar(client, token_admin, ativo_id, motivo="OUTRO", justificativa="dez carac.")

    assert resposta.status_code == 201
    assert resposta.json()["justificativa"] == "dez carac."


def test_ac029_data_de_baixa_futura_e_recusada(client, db, token_admin, ativo_id):
    amanha = (datas.hoje() + timedelta(days=1)).isoformat()

    resposta = _baixar(client, token_admin, ativo_id, data_baixa=amanha)

    _assert_recusada(resposta, db, ativo_id, "BR-022")


def test_br022_data_de_baixa_anterior_a_aquisicao_e_recusada(client, db, token_admin, ativo_id):
    resposta = _baixar(client, token_admin, ativo_id, data_baixa="2025-01-09")

    _assert_recusada(resposta, db, ativo_id, "BR-022")


def test_br022_baixa_na_data_de_aquisicao_e_aceita(client, token_admin, ativo_id):
    assert _baixar(client, token_admin, ativo_id, data_baixa=AQUISICAO).status_code == 201


def test_ac030_ativo_ja_baixado_nao_e_baixado_de_novo(client, db, token_admin, ativo_id):
    assert _baixar(client, token_admin, ativo_id).status_code == 201

    segunda = _baixar(client, token_admin, ativo_id)

    assert segunda.status_code == 409
    assert segunda.json()["regra"] == "BR-024"
    assert _total(db, BaixaAtivo) == 1
    assert _recusas(db) == [("baixa_ativo", "CRIAR", "BR-024")]


def test_ac033_baixa_sem_destinacao_e_recusada(client, db, token_admin, ativo_id):
    resposta = _baixar(client, token_admin, ativo_id, destinacao=...)

    _assert_recusada(resposta, db, ativo_id, "BR-026")


def test_destinacao_nula_tambem_e_recusada_por_br026(client, db, token_admin, ativo_id):
    resposta = _baixar(client, token_admin, ativo_id, destinacao=None)

    _assert_recusada(resposta, db, ativo_id, "BR-026")


@pytest.mark.parametrize(
    "campo,valor",
    [("motivo", "QUALQUER"), ("destinacao", "LIXO"), ("data_baixa", "ontem"), ("motivo", ...)],
)
def test_valores_fora_do_enum_ou_malformados_retornam_422(
    client, db, token_admin, ativo_id, campo, valor
):
    resposta = _baixar(client, token_admin, ativo_id, **{campo: valor})

    assert resposta.status_code == 422
    assert _total(db, BaixaAtivo) == 0


def test_br012_baixa_anterior_ao_inicio_do_vinculo_aberto_e_recusada(
    client, db, token_admin, ativo_id, responsavel, setor
):
    _vincular(client, token_admin, ativo_id, responsavel, setor, "2025-08-01")

    resposta = _baixar(client, token_admin, ativo_id, data_baixa="2025-07-10")

    assert resposta.status_code == 409
    assert resposta.json()["regra"] == "BR-012"
    assert _total(db, BaixaAtivo) == 0
    assert db.scalars(select(HistoricoTransferencia)).one().data_fim is None


def test_baixa_de_ativo_inexistente_retorna_404(client, token_admin):
    assert _baixar(client, token_admin, 999).status_code == 404


def test_ac032_baixa_preserva_todos_os_vinculos_anteriores(
    client, db, token_admin, ativo_id, responsavel, setor, outros_responsaveis
):
    _vincular(client, token_admin, ativo_id, responsavel, setor, "2025-02-01")
    _vincular(client, token_admin, ativo_id, outros_responsaveis[0], setor, "2025-04-01")
    _vincular(client, token_admin, ativo_id, outros_responsaveis[1], setor, "2025-06-01")
    antes = client.get(f"/api/v1/ativos/{ativo_id}/historico", headers=_headers(token_admin)).json()

    assert _baixar(client, token_admin, ativo_id).status_code == 201

    depois = client.get(
        f"/api/v1/ativos/{ativo_id}/historico", headers=_headers(token_admin)
    ).json()
    assert len(depois) == len(antes) == 3
    assert [v["id"] for v in depois] == [v["id"] for v in antes]
    for original, atual in zip(antes, depois, strict=True):
        assert {**original, "data_fim": None} == {**atual, "data_fim": None}
    assert depois[0]["data_fim"] == BAIXA["data_baixa"]  # só o aberto foi encerrado
    assert depois[1:] == antes[1:]


def test_ac019_depreciacao_do_baixado_usa_a_data_da_baixa_e_o_valor_congelado(
    client, db, token_admin, ativo_id
):
    antes = client.get(f"/api/v1/ativos/{ativo_id}/depreciacao", headers=_headers(token_admin))
    assert antes.json()["data_referencia"] == datas.hoje().isoformat()

    baixa = _baixar(client, token_admin, ativo_id).json()  # 2025-07-10: 6 meses de 60

    depreciacao = client.get(
        f"/api/v1/ativos/{ativo_id}/depreciacao", headers=_headers(token_admin)
    ).json()
    assert depreciacao["data_referencia"] == "2025-07-10"
    assert depreciacao["meses_decorridos"] == depreciacao["meses_efetivos"] == 6
    assert depreciacao["depreciacao_acumulada"] == "600.00"
    assert depreciacao["valor_residual"] == baixa["valor_residual_baixa"] == "5400.00"
    assert depreciacao["percentual_depreciado"] == "10.00"
    detalhe = client.get(f"/api/v1/ativos/{ativo_id}", headers=_headers(token_admin)).json()
    assert detalhe["depreciacao"] == depreciacao

    # Congelado: mudar a vida útil depois da baixa não move o valor residual persistido.
    ativo = db.get(Ativo, ativo_id)
    ativo.vida_util_meses = 12
    db.commit()
    congelado = client.get(
        f"/api/v1/ativos/{ativo_id}/depreciacao", headers=_headers(token_admin)
    ).json()
    assert congelado["valor_residual"] == "5400.00"
    assert congelado["depreciacao_acumulada"] == "600.00"
    assert congelado["percentual_depreciado"] == "10.00"
    assert Decimal(congelado["valor_compra"]) == Decimal("6000.00")


def test_baixa_apos_o_fim_da_vida_util_congela_residual_zero(
    client, db, token_admin, categoria, fornecedor
):
    criado = client.post(
        "/api/v1/ativos",
        headers=_headers(token_admin),
        json={
            "nome": "Notebook Antigo",
            "tipo": "HARDWARE",
            "categoria_id": categoria.id,
            "fornecedor_id": fornecedor.id,
            "numero_serie": "SN-ANTIGO",
            "data_aquisicao": "2015-01-10",
            "valor_compra": "6000.00",
        },
    ).json()

    baixa = _baixar(
        client, token_admin, criado["id"], data_baixa="2024-01-10", motivo="FIM_VIDA_UTIL"
    )

    assert baixa.json()["valor_residual_baixa"] == "0.00"
    depreciacao = client.get(
        f"/api/v1/ativos/{criado['id']}/depreciacao", headers=_headers(token_admin)
    ).json()
    assert depreciacao["valor_residual"] == "0.00"
    assert depreciacao["percentual_depreciado"] == "100.00"


def test_ac057_baixa_registra_auditoria_de_criacao_e_da_mudanca_de_status(
    client, db, token_admin, ativo_id, responsavel, setor
):
    vinculo = _vincular(client, token_admin, ativo_id, responsavel, setor, "2025-02-01")
    anteriores = set(db.scalars(select(AuditLog.id)))  # audit_log é imutável: não dá para limpar

    baixa = _baixar(client, token_admin, ativo_id).json()

    registros = {
        (a.operacao, a.entidade, a.entidade_id, a.resultado)
        for a in db.scalars(select(AuditLog).where(AuditLog.id.not_in(anteriores)))
    }
    assert registros == {
        ("CRIAR", "baixa_ativo", baixa["id"], "SUCESSO"),
        ("ATUALIZAR", "ativo", ativo_id, "SUCESSO"),
        ("ATUALIZAR", "historico_transferencia", vinculo["id"], "SUCESSO"),
    }


def test_ativo_baixado_continua_acessivel_e_listavel_por_filtro(client, token_admin, ativo_id):
    assert _baixar(client, token_admin, ativo_id).status_code == 201

    detalhe = client.get(f"/api/v1/ativos/{ativo_id}", headers=_headers(token_admin)).json()
    filtrado = client.get("/api/v1/ativos?status=BAIXADO", headers=_headers(token_admin)).json()
    ativos = client.get("/api/v1/ativos?status=ATIVO", headers=_headers(token_admin)).json()

    assert detalhe["status"] == "BAIXADO"
    assert [i["id"] for i in filtrado["itens"]] == [ativo_id]
    assert ativos["itens"] == []
