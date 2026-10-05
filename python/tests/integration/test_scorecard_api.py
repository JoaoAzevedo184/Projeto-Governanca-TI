"""Scorecard de fornecedores (FR-011): AC-048, AC-049 e BR-029.

Cenário-base: critérios preço (40), prazo (30) e suporte (30).
Fornecedor A: 8, 6, 9  → 8×0,4 + 6×0,3 + 9×0,3 = 3,20 + 1,80 + 2,70 = 7,70
Fornecedor B: 9, 7, 5  → 3,60 + 2,10 + 1,50 = 7,20
"""

import pytest
from prometheus_client import REGISTRY
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.models.auditoria import AuditLog
from app.models.fornecedor import Fornecedor, FornecedorAvaliacao

CRITERIOS = [
    {"nome": "preco", "peso": "40"},
    {"nome": "prazo", "peso": "30"},
    {"nome": "suporte", "peso": "30"},
]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def fornecedores(db, fornecedor):
    outros = [Fornecedor(razao_social=f"Fornecedor {n}", data_source="sintetico") for n in "BC"]
    db.add_all(outros)
    db.commit()
    return [fornecedor.id, *[f.id for f in outros]]


def _corpo(fornecedores, **sobrescritas):
    a, b = fornecedores[:2]
    corpo = {
        "periodo": "2026-T3",
        "criterios": CRITERIOS,
        "avaliacoes": [
            {"fornecedor_id": a, "notas": {"preco": "8", "prazo": "6", "suporte": "9"}},
            {"fornecedor_id": b, "notas": {"preco": "9", "prazo": "7", "suporte": "5"}},
        ],
        **sobrescritas,
    }
    return {k: v for k, v in corpo.items() if v is not ...}


def _enviar(client, token, corpo):
    return client.post("/api/v1/fornecedores/scorecard", headers=_headers(token), json=corpo)


def _violadas(regra):
    return REGISTRY.get_sample_value("itam_regras_violadas_total", {"regra": regra}) or 0.0


def _total(db, modelo):
    return db.scalar(select(func.count()).select_from(modelo))


def test_ac049_scorecard_valido_devolve_pontuacao_ponderada_e_ranking(
    client, db, token_admin, fornecedores
):
    resposta = _enviar(client, token_admin, _corpo(fornecedores))

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["periodo"] == "2026-T3"
    assert [(r["posicao"], r["fornecedor_id"], r["pontuacao"]) for r in corpo["ranking"]] == [
        (1, fornecedores[0], "7.70"),
        (2, fornecedores[1], "7.20"),
    ]
    assert corpo["ranking"][0]["razao_social"] == "Fornecedor Teste LTDA"
    assert corpo["ranking"][0]["notas"] == {"preco": "8.00", "prazo": "6.00", "suporte": "9.00"}
    assert [(c["nome"], c["peso"]) for c in corpo["criterios"]] == [
        ("preco", "40.00"),
        ("prazo", "30.00"),
        ("suporte", "30.00"),
    ]


def test_ranking_inverte_quando_o_segundo_fornecedor_pontua_mais(client, token_admin, fornecedores):
    a, b = fornecedores[:2]
    corpo = _corpo(
        fornecedores,
        avaliacoes=[
            {"fornecedor_id": a, "notas": {"preco": "5", "prazo": "5", "suporte": "5"}},
            {"fornecedor_id": b, "notas": {"preco": "10", "prazo": "10", "suporte": "10"}},
        ],
    )

    ranking = _enviar(client, token_admin, corpo).json()["ranking"]

    assert [(r["posicao"], r["fornecedor_id"], r["pontuacao"]) for r in ranking] == [
        (1, b, "10.00"),
        (2, a, "5.00"),
    ]


def test_ac049_persiste_uma_linha_por_fornecedor_e_criterio(client, db, token_admin, fornecedores):
    _enviar(client, token_admin, _corpo(fornecedores))

    linhas = db.scalars(select(FornecedorAvaliacao).order_by(FornecedorAvaliacao.id)).all()

    assert len(linhas) == 6  # 2 fornecedores × 3 critérios
    primeira = linhas[0]
    assert (primeira.fornecedor_id, primeira.criterio, primeira.periodo) == (
        fornecedores[0],
        "preco",
        "2026-T3",
    )
    assert (str(primeira.peso), str(primeira.nota), primeira.data_source) == (
        "40.00",
        "8.00",
        "manual",
    )
    assert {(x.fornecedor_id, x.criterio): str(x.nota) for x in linhas}[
        (fornecedores[1], "suporte")
    ] == "5.00"


def test_ac049_cada_fornecedor_avaliado_gera_auditoria(client, db, token_admin, fornecedores):
    _enviar(client, token_admin, _corpo(fornecedores))

    auditoria = db.scalars(
        select(AuditLog).where(AuditLog.entidade == "fornecedor_avaliacao").order_by(AuditLog.id)
    ).all()

    assert [(a.operacao, a.resultado) for a in auditoria] == [("CRIAR", "SUCESSO")] * 2
    assert [a.detalhe["fornecedor_id"] for a in auditoria] == fornecedores[:2]
    assert [a.detalhe["pontuacao"] for a in auditoria] == ["7.70", "7.20"]
    assert len(auditoria[0].detalhe["linhas"]) == 3


def test_ac048_pesos_somando_95_sao_recusados_com_a_regra_na_auditoria_e_na_metrica(
    client, db, token_admin, fornecedores
):
    criterios = [
        {"nome": "preco", "peso": "40"},
        {"nome": "prazo", "peso": "30"},
        {"nome": "suporte", "peso": "25"},
    ]
    antes = _violadas("BR-029")

    resposta = _enviar(client, token_admin, _corpo(fornecedores, criterios=criterios))

    assert resposta.status_code == 409
    corpo = resposta.json()
    assert corpo["regra"] == "BR-029"
    assert "95" in corpo["detalhe"] and "100%" in corpo["detalhe"]  # mensagem explícita
    assert _total(db, FornecedorAvaliacao) == 0  # nada gravado
    recusas = db.scalars(select(AuditLog).where(AuditLog.resultado == "RECUSADO")).all()
    assert [(a.entidade, a.operacao, a.regra_violada) for a in recusas] == [
        ("fornecedor_avaliacao", "CRIAR", "BR-029")
    ]
    assert recusas[0].detalhe["soma_dos_pesos"] == "95"
    assert _violadas("BR-029") == antes + 1


@pytest.mark.parametrize(
    "pesos", [["40", "30", "31"], ["33.33", "33.33", "33.33"], ["50", "50", "1"]]
)
def test_br029_pesos_acima_ou_abaixo_de_100_tambem_sao_recusados(
    client, token_admin, fornecedores, pesos
):
    criterios = [{"nome": n, "peso": p} for n, p in zip(["preco", "prazo", "suporte"], pesos)]

    resposta = _enviar(client, token_admin, _corpo(fornecedores, criterios=criterios))

    assert resposta.status_code == 409 and resposta.json()["regra"] == "BR-029"


def test_br029_pesos_com_casas_decimais_que_fecham_100_sao_aceitos(
    client, token_admin, fornecedores
):
    criterios = [
        {"nome": "preco", "peso": "10.10"},
        {"nome": "prazo", "peso": "20.20"},
        {"nome": "suporte", "peso": "69.70"},
    ]

    assert (
        _enviar(client, token_admin, _corpo(fornecedores, criterios=criterios)).status_code == 201
    )


@pytest.mark.parametrize(
    "notas",
    [
        {"preco": "10.01", "prazo": "6", "suporte": "9"},
        {"preco": "-0.01", "prazo": "6", "suporte": "9"},
        {"preco": "8", "prazo": "6"},  # critério sem nota
        {"preco": "8", "prazo": "6", "suporte": "9", "extra": "5"},  # critério desconhecido
        {"preco": "8.123", "prazo": "6", "suporte": "9"},
        {"preco": "oito", "prazo": "6", "suporte": "9"},
    ],
)
def test_nota_invalida_faltando_ou_desconhecida_e_422_e_nada_e_gravado(
    client, db, token_admin, fornecedores, notas
):
    avaliacoes = [{"fornecedor_id": fornecedores[0], "notas": notas}]

    resposta = _enviar(client, token_admin, _corpo(fornecedores, avaliacoes=avaliacoes))

    assert resposta.status_code == 422
    assert _total(db, FornecedorAvaliacao) == 0


def test_nota_nos_limites_0_e_10_e_aceita(client, token_admin, fornecedores):
    avaliacoes = [
        {"fornecedor_id": fornecedores[0], "notas": {"preco": "0", "prazo": "10", "suporte": "10"}}
    ]

    resposta = _enviar(client, token_admin, _corpo(fornecedores, avaliacoes=avaliacoes))

    assert resposta.status_code == 201
    assert resposta.json()["ranking"][0]["pontuacao"] == "6.00"  # 0×0,4 + 10×0,3 + 10×0,3


@pytest.mark.parametrize(
    "sobrescritas",
    [
        {"criterios": []},
        {"avaliacoes": []},
        {"criterios": [{"nome": "preco", "peso": "50"}, {"nome": "preco", "peso": "50"}]},
        {
            "criterios": [
                {"nome": "preco", "peso": "0"},
                {"nome": "prazo", "peso": "100"},
                {"nome": "suporte", "peso": "0"},
            ]
        },
        {
            "criterios": [
                {"nome": "preco", "peso": "101"},
                {"nome": "prazo", "peso": "0.01"},
                {"nome": "suporte", "peso": "0.01"},
            ]
        },
        {"periodo": ""},
        {"periodo": "x" * 21},
        {"periodo": ...},
    ],
)
def test_corpo_malformado_e_422(client, token_admin, fornecedores, sobrescritas):
    assert _enviar(client, token_admin, _corpo(fornecedores, **sobrescritas)).status_code == 422


def test_fornecedor_repetido_na_mesma_submissao_e_422(client, token_admin, fornecedores):
    nota = {"preco": "8", "prazo": "6", "suporte": "9"}
    avaliacoes = [{"fornecedor_id": fornecedores[0], "notas": nota}] * 2

    assert (
        _enviar(client, token_admin, _corpo(fornecedores, avaliacoes=avaliacoes)).status_code == 422
    )


def test_fornecedor_inexistente_e_404_sem_gravar_nada_nem_auditar(
    client, db, token_admin, fornecedores
):
    nota = {"preco": "8", "prazo": "6", "suporte": "9"}
    avaliacoes = [
        {"fornecedor_id": fornecedores[0], "notas": nota},
        {"fornecedor_id": 9999, "notas": nota},
    ]

    resposta = _enviar(client, token_admin, _corpo(fornecedores, avaliacoes=avaliacoes))

    assert resposta.status_code == 404
    assert _total(db, FornecedorAvaliacao) == 0
    assert _total(db, AuditLog) == 0


def test_o_mesmo_fornecedor_pode_ser_avaliado_em_outro_periodo(
    client, db, token_admin, fornecedores
):
    _enviar(client, token_admin, _corpo(fornecedores))

    resposta = _enviar(client, token_admin, _corpo(fornecedores, periodo="2026-T4"))

    assert resposta.status_code == 201
    assert _total(db, FornecedorAvaliacao) == 12


def test_gestor_registra_e_operador_e_auditor_recebem_403(
    client, token_gestor, token_operador, token_auditor, fornecedores
):
    assert _enviar(client, token_gestor, _corpo(fornecedores)).status_code == 201
    assert _enviar(client, token_operador, _corpo(fornecedores)).status_code == 403
    assert _enviar(client, token_auditor, _corpo(fornecedores)).status_code == 403


def test_banco_garante_nota_e_peso_validos(client, db, token_admin, fornecedores):
    _enviar(client, token_admin, _corpo(fornecedores))

    with pytest.raises(IntegrityError, match="ck_avaliacao_nota"):
        db.execute(text("UPDATE fornecedor_avaliacao SET nota = 11 WHERE id = 1"))
    db.rollback()
    with pytest.raises(IntegrityError, match="ck_avaliacao_peso"):
        db.execute(text("UPDATE fornecedor_avaliacao SET peso = 0 WHERE id = 1"))
    db.rollback()
