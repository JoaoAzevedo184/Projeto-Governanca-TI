"""Carregador de fornecedores da demonstração (D.2): `POST /fornecedores`, idempotente."""

import pytest
from sqlalchemy import func, select

from app import seed
from app.models.fornecedor import Fornecedor
from etl import carregar_fornecedores as carregador
from etl.carregar_fornecedores import ErroCarga

SENHAS = {"admin": "s-admin", "operador": "s-oper", "gestor": "s-gest", "auditor": "s-audit"}
FORNECEDORES = [
    {"razao_social": "ALFA COMERCIO LTDA", "cnpj": "11.111.111/0001-11"},
    {"razao_social": "BETA SERVICOS LTDA", "cnpj": "22.222.222/0001-22"},
]


def test_cria_os_fornecedores_com_data_source_compras_gov(client, db):
    seed.semear(db, SENHAS)

    resultado = carregador.carregar(client, "admin", SENHAS["admin"], FORNECEDORES)

    assert resultado.criados == ["11.111.111/0001-11", "22.222.222/0001-22"]
    assert resultado.existentes == []
    gravados = db.execute(
        select(Fornecedor.razao_social, Fornecedor.cnpj, Fornecedor.data_source, Fornecedor.ativo)
    ).all()
    assert sorted(gravados) == [
        ("ALFA COMERCIO LTDA", "11.111.111/0001-11", "compras_gov", True),
        ("BETA SERVICOS LTDA", "22.222.222/0001-22", "compras_gov", True),
    ]


def test_rodar_de_novo_nao_duplica_nem_falha(client, db):
    seed.semear(db, SENHAS)
    carregador.carregar(client, "admin", SENHAS["admin"], FORNECEDORES)

    segunda = carregador.carregar(client, "admin", SENHAS["admin"], FORNECEDORES)

    assert segunda.criados == [] and len(segunda.existentes) == 2
    assert db.scalar(select(func.count()).select_from(Fornecedor)) == 2


def test_completa_so_o_que_falta(client, db):
    seed.semear(db, SENHAS)
    carregador.carregar(client, "admin", SENHAS["admin"], FORNECEDORES[:1])

    resultado = carregador.carregar(client, "admin", SENHAS["admin"], FORNECEDORES)

    assert resultado.criados == ["22.222.222/0001-22"]
    assert resultado.existentes == ["11.111.111/0001-11"]


def test_login_recusado_nao_cadastra_nada_e_a_mensagem_nao_leva_a_senha(client, db):
    seed.semear(db, SENHAS)

    with pytest.raises(ErroCarga) as erro:
        carregador.carregar(client, "admin", "senha-errada", FORNECEDORES)

    assert "login recusado (HTTP 401)" in str(erro.value) and "senha-errada" not in str(erro.value)
    assert db.scalar(select(func.count()).select_from(Fornecedor)) == 0


def test_perfil_sem_permissao_e_recusado_no_cadastro(client, db):
    seed.semear(db, SENHAS)

    with pytest.raises(ErroCarga, match="HTTP 403"):
        carregador.carregar(client, "operador", SENHAS["operador"], FORNECEDORES)

    assert db.scalar(select(func.count()).select_from(Fornecedor)) == 0


def test_main_exige_as_credenciais_do_ambiente(monkeypatch, capsys):
    monkeypatch.delenv("ITAM_API_LOGIN", raising=False)
    monkeypatch.delenv("ITAM_API_SENHA", raising=False)

    codigo = carregador.main()

    assert codigo == 2 and "ITAM_API_LOGIN" in capsys.readouterr().err


def test_main_sai_com_1_quando_a_api_nao_responde(monkeypatch, capsys):
    monkeypatch.setenv("ITAM_API_LOGIN", "admin")
    monkeypatch.setenv("ITAM_API_SENHA", "x")
    monkeypatch.setenv("ITAM_API_URL", "http://127.0.0.1:9")  # porta fechada

    codigo = carregador.main()

    assert codigo == 1 and "Carga recusada" in capsys.readouterr().err


def test_le_o_csv_versionado_de_fornecedores_da_demonstracao():
    fornecedores = carregador.ler_fornecedores()

    assert len(fornecedores) == 16
    assert set(fornecedores[0]) == {"razao_social", "cnpj"}
