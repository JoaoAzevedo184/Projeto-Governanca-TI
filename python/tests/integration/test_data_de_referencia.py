"""A data de referência de Recife vale nas regras que comparam com "hoje".

Relógio controlado em 22h de Recife (01h UTC do dia seguinte) e em 02h de Recife (05h UTC): às
22h o sistema ainda está no dia de Recife, e às 02h os dois fusos coincidem. Cobre a data futura
(BR-003), a licença vencida e a depreciação, e as outras datas "não futuras" do cadastro.
"""

from datetime import UTC, datetime

import pytest

from app.utils import datas

NOITE_DE_RECIFE = datetime(2031, 3, 11, 1, 0, tzinfo=UTC)  # 22h de 10/03 em Recife
MADRUGADA_DE_RECIFE = datetime(2031, 3, 11, 5, 0, tzinfo=UTC)  # 02h de 11/03 em Recife


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def relogio(monkeypatch):
    def fixar(instante):
        monkeypatch.setattr(datas, "_agora_utc", lambda: instante)

    return fixar


def _novo_ativo(client, token, categoria, fornecedor, aquisicao, serie="SN-FUSO"):
    return client.post(
        "/api/v1/ativos",
        headers=_headers(token),
        json={
            "nome": "Notebook fuso",
            "tipo": "HARDWARE",
            "categoria_id": categoria.id,
            "fornecedor_id": fornecedor.id,
            "numero_serie": serie,
            "data_aquisicao": aquisicao,
            "valor_compra": "6000.00",
            "vida_util_meses": 60,
        },
    )


def test_br003_as_22h_de_recife_o_dia_seguinte_ainda_e_data_futura(
    client, token_admin, categoria, fornecedor, relogio
):
    relogio(NOITE_DE_RECIFE)

    futura = _novo_ativo(client, token_admin, categoria, fornecedor, "2031-03-11", "SN-A")
    de_hoje = _novo_ativo(client, token_admin, categoria, fornecedor, "2031-03-10", "SN-B")

    assert futura.status_code == 422  # 11/03 é futuro em Recife, embora já seja 11/03 em UTC
    assert "BR-003" in futura.text
    assert de_hoje.status_code == 201


def test_br003_as_2h_de_recife_o_dia_11_ja_e_hoje(
    client, token_admin, categoria, fornecedor, relogio
):
    relogio(MADRUGADA_DE_RECIFE)

    resposta = _novo_ativo(client, token_admin, categoria, fornecedor, "2031-03-11")

    assert resposta.status_code == 201


def test_br003_na_importacao_a_data_futura_tambem_e_a_de_recife(
    client, token_admin, categoria, fornecedor, relogio
):
    import io

    relogio(NOITE_DE_RECIFE)
    linhas = [
        "nome,tipo,categoria,fornecedor,numero_serie,data_aquisicao,valor_compra",
        f"Notebook A,HARDWARE,{categoria.nome},{fornecedor.razao_social},SN-1,2031-03-10,100.00",
        f"Notebook B,HARDWARE,{categoria.nome},{fornecedor.razao_social},SN-2,2031-03-11,100.00",
    ]

    resposta = client.post(
        "/api/v1/importacoes",
        headers=_headers(token_admin),
        files={"arquivo": ("i.csv", io.BytesIO(("\n".join(linhas) + "\n").encode()), "text/csv")},
    ).json()

    assert (resposta["total_aceito"], resposta["total_rejeitado"]) == (1, 1)


def test_depreciacao_as_22h_de_recife_ainda_nao_completou_o_mes(
    client, token_admin, categoria, fornecedor, relogio
):
    """6.000 em 60 meses, comprado em 11/03/2030: faltam 2 horas de UTC para o dia 11 em Recife.
    Em 10/03/2031 são 11 meses completos (residual 6.000 - 6.000 x 11 / 60 = 4.900,00); em
    11/03/2031, 12 meses (residual 4.800,00)."""
    relogio(datetime(2030, 3, 12, 12, 0, tzinfo=UTC))
    ativo = _novo_ativo(client, token_admin, categoria, fornecedor, "2030-03-11").json()["id"]

    relogio(NOITE_DE_RECIFE)
    noite = client.get(f"/api/v1/ativos/{ativo}/depreciacao", headers=_headers(token_admin)).json()
    relogio(MADRUGADA_DE_RECIFE)
    madrugada = client.get(
        f"/api/v1/ativos/{ativo}/depreciacao", headers=_headers(token_admin)
    ).json()

    assert (noite["meses_decorridos"], noite["valor_residual"]) == (11, "4900.00")
    assert (madrugada["meses_decorridos"], madrugada["valor_residual"]) == (12, "4800.00")


def _licenca(client, token, fornecedor, expiracao):
    return client.post(
        "/api/v1/licencas",
        headers=_headers(token),
        json={
            "tipo_licenciamento": "SUBSCRICAO",
            "software": "Software de fuso",
            "fornecedor_id": fornecedor.id,
            "chave_licenca": "FUSO-0001-0002-0003",
            "quantidade_contratada": 1,
            "valor_total": "10.00",
            "data_inicio_vigencia": "2030-01-01",
            "data_expiracao": expiracao,
        },
    )


def _codigos(client, token):
    alertas = client.get("/api/v1/compliance/alertas", headers=_headers(token)).json()
    return [
        a["codigo"] for g in alertas["grupos"] for a in g["alertas"] if a["entidade"] == "licenca"
    ]


def test_licenca_vencida_so_depois_da_meia_noite_de_recife(
    client, token_admin, fornecedor, relogio
):
    relogio(datetime(2030, 6, 1, 12, 0, tzinfo=UTC))
    assert _licenca(client, token_admin, fornecedor, "2031-03-10").status_code == 201

    relogio(NOITE_DE_RECIFE)  # 10/03 em Recife: vence hoje, ainda não venceu
    noite = _codigos(client, token_admin)
    relogio(MADRUGADA_DE_RECIFE)  # 11/03: venceu ontem
    madrugada = _codigos(client, token_admin)

    assert noite == ["CP-03"]  # dentro da janela de alerta, não vencida
    assert madrugada == ["CP-01"]  # vencida (Crítico)


def test_licenca_vencida_nao_recebe_vinculo_so_a_partir_do_dia_de_recife(
    client, token_admin, categoria, fornecedor, relogio
):
    relogio(datetime(2030, 6, 1, 12, 0, tzinfo=UTC))
    licenca = _licenca(client, token_admin, fornecedor, "2031-03-10").json()["id"]
    maquina_a = _novo_ativo(client, token_admin, categoria, fornecedor, "2030-05-01", "SN-A").json()
    maquina_b = _novo_ativo(client, token_admin, categoria, fornecedor, "2030-05-01", "SN-B").json()
    url = f"/api/v1/licencas/{licenca}/vinculos"

    relogio(NOITE_DE_RECIFE)  # 10/03 em Recife: último dia de vigência
    no_ultimo_dia = client.post(
        url, headers=_headers(token_admin), json={"ativo_id": maquina_a["id"]}
    )
    relogio(MADRUGADA_DE_RECIFE)  # 11/03: venceu
    depois = client.post(url, headers=_headers(token_admin), json={"ativo_id": maquina_b["id"]})

    assert no_ultimo_dia.status_code == 201
    assert (depois.status_code, depois.json()["regra"]) == (409, "BR-020")


def test_data_de_inicio_de_vinculo_e_de_vigencia_tambem_seguem_recife(
    client, token_admin, categoria, fornecedor, relogio
):
    relogio(NOITE_DE_RECIFE)

    licenca_futura = client.post(
        "/api/v1/licencas",
        headers=_headers(token_admin),
        json={
            "tipo_licenciamento": "SUBSCRICAO",
            "software": "Futuro",
            "fornecedor_id": fornecedor.id,
            "chave_licenca": "FUT-0001-0002",
            "quantidade_contratada": 1,
            "valor_total": "10.00",
            "data_inicio_vigencia": "2031-03-11",
            "data_expiracao": "2032-03-11",
        },
    )

    assert licenca_futura.status_code == 422  # início de vigência no futuro de Recife


def test_vinculo_de_responsavel_futuro_e_o_de_recife(
    client, token_admin, categoria, fornecedor, responsavel, setor, relogio
):
    relogio(datetime(2030, 6, 1, 12, 0, tzinfo=UTC))
    ativo = _novo_ativo(client, token_admin, categoria, fornecedor, "2030-05-01").json()["id"]
    url = f"/api/v1/ativos/{ativo}/responsavel"
    corpo = {"responsavel_id": responsavel.id, "setor_id": setor.id}

    relogio(NOITE_DE_RECIFE)
    futuro = client.post(
        url, headers=_headers(token_admin), json={**corpo, "data_inicio": "2031-03-11"}
    )
    de_hoje = client.post(
        url, headers=_headers(token_admin), json={**corpo, "data_inicio": "2031-03-10"}
    )

    assert futuro.status_code == 422
    assert de_hoje.status_code == 201


def test_data_do_vinculo_de_licenca_futura_e_a_de_recife(
    client, token_admin, categoria, fornecedor, relogio
):
    relogio(datetime(2030, 6, 1, 12, 0, tzinfo=UTC))
    licenca = _licenca(client, token_admin, fornecedor, "2032-01-01").json()["id"]
    maquina = _novo_ativo(client, token_admin, categoria, fornecedor, "2030-05-01").json()["id"]
    url = f"/api/v1/licencas/{licenca}/vinculos"

    relogio(NOITE_DE_RECIFE)
    futura = client.post(
        url, headers=_headers(token_admin), json={"ativo_id": maquina, "data_vinculo": "2031-03-11"}
    )
    de_hoje = client.post(
        url, headers=_headers(token_admin), json={"ativo_id": maquina, "data_vinculo": "2031-03-10"}
    )

    assert futura.status_code == 422
    assert de_hoje.status_code == 201


def test_data_da_recomendacao_futura_e_a_de_recife(client, token_admin, responsavel, relogio):
    relogio(NOITE_DE_RECIFE)
    corpo = {
        "titulo": "Renovar contrato",
        "contexto": "Contexto",
        "recomendacao": "Renovar",
        "responsavel_id": responsavel.id,
        "evidencias": [{"tipo": "PREMISSA", "descricao": "Premissa de teste"}],
    }

    futura = client.post(
        "/api/v1/recomendacoes", headers=_headers(token_admin), json={**corpo, "data": "2031-03-11"}
    )
    de_hoje = client.post(
        "/api/v1/recomendacoes", headers=_headers(token_admin), json={**corpo, "data": "2031-03-10"}
    )

    assert futura.status_code == 422
    assert de_hoje.status_code == 201
