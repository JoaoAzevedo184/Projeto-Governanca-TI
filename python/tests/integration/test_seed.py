"""Seed mínimo de demonstração (docs/modelo-de-dados/dados-semente.md): usuários e categorias."""

import pytest
from sqlalchemy import func, select

from app import seed
from app.models.auditoria import AuditLog
from app.models.categoria import Categoria
from app.models.usuario import Usuario

SENHAS = {"admin": "s-admin", "operador": "s-oper", "gestor": "s-gest", "auditor": "s-audit"}


def _total(db, modelo) -> int:
    return db.scalar(select(func.count()).select_from(modelo))


def test_seed_cria_os_quatro_usuarios_e_as_categorias(db):
    criados = seed.semear(db, SENHAS)

    assert criados == {"usuarios": 4, "categorias": 11}
    perfis = dict(db.execute(select(Usuario.login, Usuario.perfil)).all())
    assert perfis == {
        "admin": "ADMIN",
        "operador": "OPERADOR",
        "gestor": "GESTOR",
        "auditor": "AUDITOR",
    }
    categorias = {
        c.nome: (c.tipo_aplicavel, c.vida_util_meses) for c in db.scalars(select(Categoria))
    }
    assert len(categorias) == 11
    assert categorias["Notebook"] == ("HARDWARE", 60)
    assert categorias["Impressora"] == ("HARDWARE", 48)
    assert categorias["Smartphone"] == ("HARDWARE", 36)
    assert categorias["Software perpétuo"] == ("SOFTWARE", 60)


def test_seed_grava_hash_e_audita_cada_criacao(db):
    seed.semear(db, SENHAS)

    for usuario in db.scalars(select(Usuario)):
        assert usuario.senha_hash.startswith("$2")
        assert SENHAS[usuario.login] not in usuario.senha_hash
    assert _total(db, AuditLog) == 15
    auditoria = db.scalars(select(AuditLog)).all()
    assert {a.operacao for a in auditoria} == {"CRIAR"}
    assert {a.entidade for a in auditoria} == {"usuario", "categoria"}
    assert all(a.detalhe == {"origem": "seed"} for a in auditoria)


def test_seed_e_idempotente_e_nao_altera_o_existente(db):
    seed.semear(db, SENHAS)
    hash_admin = db.scalar(select(Usuario.senha_hash).where(Usuario.login == "admin"))

    segunda = seed.semear(db, {login: "outra" for login in SENHAS})

    assert segunda == {"usuarios": 0, "categorias": 0}
    assert _total(db, Usuario) == 4
    assert _total(db, Categoria) == 11
    assert _total(db, AuditLog) == 15
    assert db.scalar(select(Usuario.senha_hash).where(Usuario.login == "admin")) == hash_admin


def test_seed_complementa_o_que_falta(db):
    db.add(Categoria(nome="Notebook", tipo_aplicavel="HARDWARE", vida_util_meses=60))
    db.commit()

    criados = seed.semear(db, SENHAS)

    assert criados == {"usuarios": 4, "categorias": 10}


def test_login_com_usuario_criado_pelo_seed(client, db):
    seed.semear(db, SENHAS)

    ok = client.post("/api/v1/auth/login", json={"login": "operador", "senha": "s-oper"})
    assert ok.status_code == 200
    token = ok.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["perfil"] == "OPERADOR"

    errado = client.post("/api/v1/auth/login", json={"login": "operador", "senha": "admin"})
    assert errado.status_code == 401


def test_main_semeia_a_partir_das_variaveis_de_ambiente(db, monkeypatch, capsys):
    for login, senha in SENHAS.items():
        monkeypatch.setenv(f"SEED_{login.upper()}_PASSWORD", senha)

    seed.main()

    assert "4 usuário(s) e 11 categoria(s)" in capsys.readouterr().out
    assert _total(db, Usuario) == 4


def test_main_recusa_senha_ausente(db, monkeypatch):
    for login in SENHAS:
        monkeypatch.delenv(f"SEED_{login.upper()}_PASSWORD", raising=False)

    with pytest.raises(SystemExit, match="SEED_ADMIN_PASSWORD"):
        seed.main()
    assert _total(db, Usuario) == 0


def test_main_recusa_ambiente_de_producao(db, monkeypatch):
    for login, senha in SENHAS.items():
        monkeypatch.setenv(f"SEED_{login.upper()}_PASSWORD", senha)
    monkeypatch.setenv("ENVIRONMENT", "producao")

    with pytest.raises(SystemExit, match="producao"):
        seed.main()
    assert _total(db, Usuario) == 0
