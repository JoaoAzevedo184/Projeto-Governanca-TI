"""Painel de compliance (FR-007): AC-022, AC-023, AC-039 a AC-043; status e alertas da licença.

Datas relativas a hoje: a API lê o relógio de `hoje()`, então o esperado é calculado a partir
da mesma data, e os limites exatos ficam em `tests/unit/test_conformidade.py`.
"""

from datetime import date, timedelta

import pytest
from sqlalchemy import update

from app.core.config import get_settings
from app.models.ativo import Ativo
from app.models.enums import StatusAtivo
from app.models.licenca import LicencaVinculo


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _em(dias: int) -> str:
    return (date.today() + timedelta(days=dias)).isoformat()


def _alertas(client, token, **params):
    resposta = client.get("/api/v1/compliance/alertas", headers=_headers(token), params=params)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def _do_painel(painel, codigo, entidade_id=None):
    return [
        a
        for g in painel["grupos"]
        for a in g["alertas"]
        if a["codigo"] == codigo and (entidade_id is None or a["entidade_id"] == entidade_id)
    ]


def _vincular_direto(db, licenca_id, ativo_id):
    """Vínculo gravado direto no banco: a API recusaria o excedente (BR-018); aqui interessa o
    painel enxergar o estado, que só um escritor externo (ETL, carga) provoca."""
    db.add(
        LicencaVinculo(
            licenca_id=licenca_id,
            ativo_id=ativo_id,
            data_vinculo=date.today(),
            ativo_vinculo=True,
            data_source="manual",
        )
    )
    db.commit()


def _atribuir(client, token, ativo_id, responsavel, setor):
    resposta = client.post(
        f"/api/v1/ativos/{ativo_id}/responsavel",
        headers=_headers(token),
        json={"responsavel_id": responsavel.id, "setor_id": setor.id, "data_inicio": "2025-02-01"},
    )
    assert resposta.status_code == 201, resposta.text


def test_ac022_licenca_expirando_em_25_dias_aparece_como_alto(client, token_admin, nova_licenca):
    licenca = nova_licenca(expiracao=_em(25))

    painel = _alertas(client, token_admin)

    (alerta,) = _do_painel(painel, "CP-03", licenca)
    assert alerta["severidade"] == "ALTO"
    assert alerta["entidade"] == "licenca"
    assert _do_painel(painel, "CP-01", licenca) == []  # ainda não venceu


def test_ac023_licenca_vencida_aparece_como_critico(client, token_admin, nova_licenca):
    licenca = nova_licenca(expiracao=_em(-1))

    painel = _alertas(client, token_admin)

    (alerta,) = _do_painel(painel, "CP-01", licenca)
    assert alerta["severidade"] == "CRITICO"
    assert _do_painel(painel, "CP-03", licenca) == []  # vencida não é "a vencer"


def test_cp02_uso_acima_do_contratado_e_critico(client, db, token_admin, nova_licenca, novo_ativo):
    licenca = nova_licenca(quantidade=1)
    _vincular_direto(db, licenca, novo_ativo())
    _vincular_direto(db, licenca, novo_ativo())

    painel = _alertas(client, token_admin)

    (alerta,) = _do_painel(painel, "CP-02", licenca)
    assert alerta["severidade"] == "CRITICO"
    assert (
        client.get(f"/api/v1/licencas/{licenca}", headers=_headers(token_admin)).json()[
            "status_conformidade"
        ]
        == "NAO_CONFORME"
    )


def test_licenca_no_limite_do_contratado_nao_dispara_cp02(
    client, db, token_admin, nova_licenca, novo_ativo
):
    licenca = nova_licenca(quantidade=2)
    _vincular_direto(db, licenca, novo_ativo())
    _vincular_direto(db, licenca, novo_ativo())

    assert _do_painel(_alertas(client, token_admin), "CP-02", licenca) == []


def test_baixa_da_maquina_tira_o_cp02_porque_o_vinculo_encerrado_nao_conta(
    client, db, token_admin, nova_licenca, novo_ativo
):
    licenca = nova_licenca(quantidade=1)
    primeira, segunda = novo_ativo(), novo_ativo()
    _vincular_direto(db, licenca, primeira)
    _vincular_direto(db, licenca, segunda)
    assert _do_painel(_alertas(client, token_admin), "CP-02", licenca)

    baixa = client.post(
        f"/api/v1/ativos/{segunda}/baixa",
        headers=_headers(token_admin),
        json={"motivo": "DEFEITO", "data_baixa": "2025-07-10", "destinacao": "DESCARTE"},
    )

    assert baixa.status_code == 201
    assert _do_painel(_alertas(client, token_admin), "CP-02", licenca) == []


def test_licenca_e_resposta_trazem_status_conformidade_e_alertas(client, token_admin, nova_licenca):
    em_dia, a_vencer, vencida = (
        nova_licenca(),
        nova_licenca(expiracao=_em(10)),
        nova_licenca(expiracao=_em(-5)),
    )

    def estado(licenca):
        corpo = client.get(f"/api/v1/licencas/{licenca}", headers=_headers(token_admin)).json()
        return corpo["status_conformidade"], corpo["alertas"]

    assert estado(em_dia) == ("CONFORME", [])
    assert estado(a_vencer) == ("ALERTA", ["CP-03"])
    assert estado(vencida) == ("NAO_CONFORME", ["CP-01"])
    listagem = client.get("/api/v1/licencas", headers=_headers(token_admin)).json()["itens"]
    assert {i["id"]: i["status_conformidade"] for i in listagem} == {
        em_dia: "CONFORME",
        a_vencer: "ALERTA",
        vencida: "NAO_CONFORME",
    }


def test_janela_de_alerta_vem_da_configuracao(client, token_admin, nova_licenca, monkeypatch):
    licenca = nova_licenca(expiracao=_em(45))
    assert _do_painel(_alertas(client, token_admin), "CP-03", licenca) == []

    monkeypatch.setattr(get_settings(), "janela_alerta_licenca_dias", 60)

    assert _do_painel(_alertas(client, token_admin), "CP-03", licenca)


def test_ac039_ativo_ativo_sem_responsavel_dispara_cp04_como_alto(client, token_admin, novo_ativo):
    ativo = novo_ativo()

    painel = _alertas(client, token_admin)

    (alerta,) = _do_painel(painel, "CP-04", ativo)
    assert alerta["severidade"] == "ALTO"
    assert alerta["entidade"] == "ativo"


def test_cp04_so_vale_para_ativo_com_status_ativo(client, db, token_admin, novo_ativo):
    manutencao, baixado, operando = novo_ativo(), novo_ativo(), novo_ativo()
    db.execute(update(Ativo).where(Ativo.id == manutencao).values(status=StatusAtivo.EM_MANUTENCAO))
    db.commit()
    client.post(
        f"/api/v1/ativos/{baixado}/baixa",
        headers=_headers(token_admin),
        json={"motivo": "DEFEITO", "data_baixa": "2025-07-10", "destinacao": "DESCARTE"},
    )

    ids = {a["entidade_id"] for a in _do_painel(_alertas(client, token_admin), "CP-04")}

    assert ids == {operando}


def test_ac040_alertas_agrupados_por_severidade_em_ordem_decrescente(
    client, token_admin, nova_licenca, novo_ativo
):
    nova_licenca(expiracao=_em(10))  # ALTO (CP-03)
    nova_licenca(expiracao=_em(-1))  # CRITICO (CP-01)
    novo_ativo()  # ALTO (CP-04)

    painel = _alertas(client, token_admin)

    assert [g["severidade"] for g in painel["grupos"]] == ["CRITICO", "ALTO"]
    assert painel["por_severidade"] == {"CRITICO": 1, "ALTO": 2, "MEDIO": 0, "BAIXO": 0}
    assert painel["total"] == 3
    assert [g["total"] for g in painel["grupos"]] == [1, 2]
    for grupo in painel["grupos"]:
        assert {a["severidade"] for a in grupo["alertas"]} == {grupo["severidade"]}


def test_ac041_alerta_leva_ao_registro_de_origem(client, token_admin, nova_licenca, novo_ativo):
    licenca = nova_licenca(expiracao=_em(-1))
    ativo = novo_ativo()
    painel = _alertas(client, token_admin)

    (de_licenca,) = _do_painel(painel, "CP-01", licenca)
    (de_ativo,) = _do_painel(painel, "CP-04", ativo)

    assert de_licenca["link"] == f"/api/v1/licencas/{licenca}"
    assert de_ativo["link"] == f"/api/v1/ativos/{ativo}"
    for alerta, entidade_id in ((de_licenca, licenca), (de_ativo, ativo)):
        origem = client.get(alerta["link"], headers=_headers(token_admin))
        assert origem.status_code == 200
        assert origem.json()["id"] == entidade_id


@pytest.mark.parametrize(
    ("codigo", "trecho"),
    [
        ("CP-01", "data_expiracao < hoje"),
        ("CP-02", "quantidade_em_uso > quantidade_contratada"),
        ("CP-03", "janela de alerta"),
        ("CP-04", "sem vínculo de responsável aberto"),
    ],
)
def test_ac042_alerta_exibe_a_regra_que_o_originou(
    client, db, token_admin, nova_licenca, novo_ativo, codigo, trecho
):
    if codigo == "CP-01":
        nova_licenca(expiracao=_em(-1))
    elif codigo == "CP-02":
        licenca = nova_licenca(quantidade=1)
        _vincular_direto(db, licenca, novo_ativo())
        _vincular_direto(db, licenca, novo_ativo())
    elif codigo == "CP-03":
        nova_licenca(expiracao=_em(5))
    else:
        novo_ativo()

    alerta = _do_painel(_alertas(client, token_admin), codigo)[0]

    assert trecho in alerta["regra"]
    assert alerta["mensagem"]


def test_ac043_alerta_some_quando_a_nao_conformidade_e_corrigida(
    client, token_admin, nova_licenca, novo_ativo, responsavel, setor
):
    licenca = nova_licenca(expiracao=_em(-1))
    ativo = novo_ativo()
    antes = _alertas(client, token_admin)
    assert _do_painel(antes, "CP-01", licenca) and _do_painel(antes, "CP-04", ativo)

    _atribuir(client, token_admin, ativo, responsavel, setor)
    renovada = client.patch(
        f"/api/v1/licencas/{licenca}",
        headers=_headers(token_admin),
        json={"data_expiracao": _em(365)},
    )
    assert renovada.status_code == 200, renovada.text

    depois = _alertas(client, token_admin)
    assert _do_painel(depois, "CP-01", licenca) == []
    assert _do_painel(depois, "CP-04", ativo) == []
    assert depois["total"] == 0


def test_painel_vazio_sem_nao_conformidades(client, token_admin):
    painel = _alertas(client, token_admin)

    assert painel["total"] == 0
    assert painel["grupos"] == []
    assert painel["por_severidade"] == {"CRITICO": 0, "ALTO": 0, "MEDIO": 0, "BAIXO": 0}
