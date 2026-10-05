"""Registro de riscos (FR-012): AC-050 e o contrato §6.7."""

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.models.auditoria import AuditLog
from app.models.risco import Risco


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _corpo(**sobrescritas):
    corpo = {
        "titulo": "Fim de suporte do sistema operacional",
        "categoria": "SEGURANCA",
        "probabilidade": 4,
        "impacto": 5,
        "resposta": "MITIGAR",
        **sobrescritas,
    }
    return {k: v for k, v in corpo.items() if v is not ...}


def _criar(client, token, **sobrescritas):
    return client.post("/api/v1/riscos", headers=_headers(token), json=_corpo(**sobrescritas))


def test_ac050_probabilidade_4_e_impacto_5_dao_score_20_e_classificacao_critico(
    client, db, token_admin
):
    resposta = _criar(client, token_admin)

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["score"] == 20  # 4 × 5
    assert corpo["classificacao"] == "CRITICO"
    assert (corpo["probabilidade"], corpo["impacto"]) == (4, 5)
    assert corpo["status"] == "ABERTO" and corpo["data_source"] == "manual"
    assert db.scalar(select(Risco.score).where(Risco.id == corpo["id"])) == 20  # gerado pelo banco


@pytest.mark.parametrize(
    ("p", "i", "score", "classe"),
    [
        (1, 1, 1, "BAIXO"),
        (2, 2, 4, "BAIXO"),
        (1, 5, 5, "MEDIO"),
        (3, 3, 9, "MEDIO"),
        (2, 5, 10, "ALTO"),
        (3, 4, 12, "ALTO"),
        (3, 5, 15, "CRITICO"),
        (5, 5, 25, "CRITICO"),
    ],
)
def test_classificacao_em_todas_as_faixas(client, token_admin, p, i, score, classe):
    corpo = _criar(client, token_admin, probabilidade=p, impacto=i).json()

    assert (corpo["score"], corpo["classificacao"]) == (score, classe)


@pytest.mark.parametrize("campo", ["probabilidade", "impacto"])
@pytest.mark.parametrize("valor", [0, 6, -1])
def test_probabilidade_e_impacto_fora_de_1_a_5_sao_422_e_nada_e_gravado(
    client, db, token_admin, campo, valor
):
    resposta = _criar(client, token_admin, **{campo: valor})

    assert resposta.status_code == 422
    assert db.scalars(select(Risco)).all() == []


def test_score_informado_pelo_cliente_e_ignorado(client, token_admin):
    corpo = _criar(client, token_admin, score=1, classificacao="BAIXO").json()

    assert corpo["score"] == 20 and corpo["classificacao"] == "CRITICO"


@pytest.mark.parametrize(
    "invalido",
    [
        {"categoria": "OUTRA"},
        {"resposta": "IGNORAR"},
        {"status": "FECHADO"},
        {"titulo": "ab"},
        {"data_revisao": "31/12/2026"},
        {"categoria": ...},
        {"resposta": ...},
    ],
)
def test_campos_invalidos_ou_ausentes_sao_422(client, token_admin, invalido):
    assert _criar(client, token_admin, **invalido).status_code == 422


def test_cria_com_todos_os_campos_opcionais(client, token_admin, responsavel):
    resposta = _criar(
        client,
        token_admin,
        descricao="Windows 10 sem atualizações a partir de outubro",
        responsavel_id=responsavel.id,
        status="EM_TRATAMENTO",
        gatilho="Fim do suporte do fabricante",
        data_revisao="2026-12-31",
    )

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["responsavel_id"] == responsavel.id and corpo["status"] == "EM_TRATAMENTO"
    assert (corpo["gatilho"], corpo["data_revisao"]) == (
        "Fim do suporte do fabricante",
        "2026-12-31",
    )


def test_responsavel_inexistente_e_404(client, db, token_admin):
    resposta = _criar(client, token_admin, responsavel_id=999)

    assert resposta.status_code == 404
    assert db.scalars(select(Risco)).all() == []


def test_patch_recalcula_score_e_classificacao(client, db, token_admin):
    risco = _criar(client, token_admin).json()["id"]

    resposta = client.patch(
        f"/api/v1/riscos/{risco}", headers=_headers(token_admin), json={"impacto": 2}
    )

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert (corpo["score"], corpo["classificacao"]) == (8, "MEDIO")  # 4 × 2
    assert corpo["titulo"] == "Fim de suporte do sistema operacional"  # o resto não muda


def test_patch_edita_outros_campos_e_ignora_nulo_em_campo_obrigatorio(
    client, token_admin, responsavel
):
    risco = _criar(client, token_admin).json()["id"]

    corpo = client.patch(
        f"/api/v1/riscos/{risco}",
        headers=_headers(token_admin),
        json={
            "status": "ENCERRADO",
            "responsavel_id": responsavel.id,
            "gatilho": "novo gatilho",
            "titulo": None,
        },
    ).json()

    assert corpo["status"] == "ENCERRADO" and corpo["responsavel_id"] == responsavel.id
    assert corpo["gatilho"] == "novo gatilho"
    assert corpo["titulo"] == "Fim de suporte do sistema operacional"
    limpo = client.patch(
        f"/api/v1/riscos/{risco}", headers=_headers(token_admin), json={"responsavel_id": None}
    ).json()
    assert limpo["responsavel_id"] is None


def test_patch_com_responsavel_inexistente_e_404_e_risco_inexistente_tambem(client, token_admin):
    risco = _criar(client, token_admin).json()["id"]

    assert (
        client.patch(
            f"/api/v1/riscos/{risco}", headers=_headers(token_admin), json={"responsavel_id": 999}
        ).status_code
        == 404
    )
    assert (
        client.patch(
            "/api/v1/riscos/999", headers=_headers(token_admin), json={"impacto": 1}
        ).status_code
        == 404
    )
    assert client.get("/api/v1/riscos/999", headers=_headers(token_admin)).status_code == 404


def test_listagem_ordena_por_score_filtra_e_pagina(client, token_admin):
    baixo = _criar(client, token_admin, titulo="Risco baixo", probabilidade=1, impacto=2).json()
    critico = _criar(client, token_admin, titulo="Risco critico", probabilidade=5, impacto=5).json()
    medio = _criar(
        client, token_admin, titulo="Risco medio", probabilidade=2, impacto=3, categoria="LEGAL"
    ).json()

    todos = client.get("/api/v1/riscos", headers=_headers(token_admin)).json()
    assert [r["id"] for r in todos["itens"]] == [critico["id"], medio["id"], baixo["id"]]
    assert (todos["total"], todos["pagina"], todos["total_paginas"]) == (3, 1, 1)

    def ids(**params):
        resposta = client.get("/api/v1/riscos", headers=_headers(token_admin), params=params)
        return [r["id"] for r in resposta.json()["itens"]]

    assert ids(classificacao="CRITICO") == [critico["id"]]
    assert ids(classificacao="MEDIO") == [medio["id"]]
    assert ids(categoria="LEGAL") == [medio["id"]]
    assert ids(status="ENCERRADO") == []
    pagina2 = client.get(
        "/api/v1/riscos", headers=_headers(token_admin), params={"tamanho": 2, "pagina": 2}
    ).json()
    assert [r["id"] for r in pagina2["itens"]] == [baixo["id"]] and pagina2["total_paginas"] == 2


def test_gestor_escreve_e_auditor_e_operador_so_leem_ou_nem_isso(
    client, token_gestor, token_auditor, token_operador
):
    assert _criar(client, token_gestor).status_code == 201
    assert _criar(client, token_auditor).status_code == 403  # AC-055: auditor não escreve
    assert _criar(client, token_operador).status_code == 403
    assert client.get("/api/v1/riscos", headers=_headers(token_auditor)).status_code == 200
    assert client.get("/api/v1/riscos/1", headers=_headers(token_operador)).status_code == 200


def test_ac057_escritas_de_risco_geram_auditoria(client, db, token_admin):
    risco = _criar(client, token_admin).json()["id"]
    client.patch(f"/api/v1/riscos/{risco}", headers=_headers(token_admin), json={"impacto": 1})

    linhas = [
        (a.operacao, a.entidade, a.entidade_id, a.resultado)
        for a in db.scalars(
            select(AuditLog).where(AuditLog.entidade == "risco").order_by(AuditLog.id)
        )
    ]

    assert linhas == [
        ("CRIAR", "risco", risco, "SUCESSO"),
        ("ATUALIZAR", "risco", risco, "SUCESSO"),
    ]


def test_banco_garante_faixa_e_score_gerado(client, db, token_admin):
    risco = _criar(client, token_admin).json()["id"]

    with pytest.raises(IntegrityError, match="ck_risco_probabilidade"):
        db.execute(text("UPDATE risco SET probabilidade = 6 WHERE id = :i"), {"i": risco})
    db.rollback()
    with pytest.raises(Exception, match="score"):  # coluna gerada: não aceita escrita direta
        db.execute(text("UPDATE risco SET score = 1 WHERE id = :i"), {"i": risco})
    db.rollback()
