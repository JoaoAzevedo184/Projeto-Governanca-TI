"""Seed mínimo de demonstração: usuários e categorias de docs/modelo-de-dados/dados-semente.md.

Uso: `python -m app.seed` (depois de `alembic upgrade head`). Idempotente: o que já existe, por
login ou por nome, não é alterado nem duplicado. Não carrega dados do pipeline (dataset/).
As senhas vêm das variáveis SEED_<PERFIL>_PASSWORD (.env); nunca ficam no código.
"""

import os
from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import registrar_auditoria
from app.core.database import SessionLocal
from app.core.security import hash_senha
from app.models.categoria import Categoria
from app.models.enums import PerfilUsuario, TipoAtivo
from app.models.usuario import Usuario

# (nome, tipo, vida útil em meses) — IN RFB nº 1.700/2017, dados-semente.md §7.
CATEGORIAS = [
    ("Notebook", TipoAtivo.HARDWARE, 60),
    ("Desktop", TipoAtivo.HARDWARE, 60),
    ("Servidor", TipoAtivo.HARDWARE, 60),
    ("Monitor", TipoAtivo.HARDWARE, 60),
    ("Switch", TipoAtivo.HARDWARE, 60),
    ("Roteador", TipoAtivo.HARDWARE, 60),
    ("Impressora", TipoAtivo.HARDWARE, 48),
    ("Smartphone", TipoAtivo.HARDWARE, 36),
    ("Tablet", TipoAtivo.HARDWARE, 36),
    ("Nobreak", TipoAtivo.HARDWARE, 60),
    ("Software perpétuo", TipoAtivo.SOFTWARE, 60),
]

# Um usuário por perfil; o login é o perfil em minúsculas (README.md).
USUARIOS = [(perfil.value.lower(), perfil) for perfil in PerfilUsuario]


def _variavel_senha(login: str) -> str:
    return f"SEED_{login.upper()}_PASSWORD"


def semear(db: Session, senhas: Mapping[str, str]) -> dict[str, int]:
    """Cria usuários e categorias ausentes; devolve quantos foram criados de cada um.

    `senhas` mapeia o login para a senha em texto; só o hash é gravado. Cada criação entra na
    trilha de auditoria (BR-030) sem autor (`usuario_id` nulo): no primeiro usuário ainda não
    existe ninguém para assinar, e `audit_log.usuario_id` é opcional.
    """
    criados = {"usuarios": 0, "categorias": 0}

    for login, perfil in USUARIOS:
        if db.scalar(select(Usuario).where(Usuario.login == login)) is not None:
            continue
        usuario = Usuario(
            login=login, nome=login.title(), perfil=perfil, senha_hash=hash_senha(senhas[login])
        )
        db.add(usuario)
        db.flush()
        registrar_auditoria(
            db,
            usuario_id=None,
            operacao="CRIAR",
            entidade="usuario",
            entidade_id=usuario.id,
            detalhe={"origem": "seed"},
        )
        criados["usuarios"] += 1

    for nome, tipo, vida_util_meses in CATEGORIAS:
        if db.scalar(select(Categoria).where(Categoria.nome == nome)) is not None:
            continue
        categoria = Categoria(nome=nome, tipo_aplicavel=tipo, vida_util_meses=vida_util_meses)
        db.add(categoria)
        db.flush()
        registrar_auditoria(
            db,
            usuario_id=None,
            operacao="CRIAR",
            entidade="categoria",
            entidade_id=categoria.id,
            detalhe={"origem": "seed"},
        )
        criados["categorias"] += 1

    db.commit()
    return criados


def main() -> None:
    if os.environ.get("ENVIRONMENT") == "producao":
        raise SystemExit(
            "Seed recusado: usuários de demonstração não entram com ENVIRONMENT=producao."
        )
    senhas = {login: os.environ.get(_variavel_senha(login), "") for login, _ in USUARIOS}
    ausentes = [_variavel_senha(login) for login, senha in senhas.items() if not senha]
    if ausentes:
        raise SystemExit(f"Seed recusado: defina {', '.join(ausentes)} (ver .env.example).")
    with SessionLocal() as db:
        criados = semear(db, senhas)
    print(f"Seed: {criados['usuarios']} usuário(s) e {criados['categorias']} categoria(s) criados.")


if __name__ == "__main__":
    main()
