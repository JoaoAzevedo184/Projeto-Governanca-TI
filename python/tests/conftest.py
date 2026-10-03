"""Fixtures da suíte. Todos os testes rodam contra PostgreSQL 16 (item 13 da resolução do
Sprint 2): o schema vem de `alembic upgrade head`, nunca de `create_all`, para que trigger,
índice parcial e CHECK existam de verdade. Ver docs/guia/testes.md.
"""

import itertools
import os

from sqlalchemy.engine import make_url

# Antes de qualquer import de `app`: o engine é criado na importação e as settings são cacheadas.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://itam:itam@localhost:5432/itam_test"
)
# Cada teste trunca todas as tabelas: recusar qualquer banco que não seja de teste.
if not (make_url(TEST_DATABASE_URL).database or "").endswith("_test"):
    raise RuntimeError(f"TEST_DATABASE_URL deve apontar para um banco *_test: {TEST_DATABASE_URL}")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.database import SessionLocal, engine, get_db  # noqa: E402
from app.core.logging import configurar_logging  # noqa: E402
from app.core.security import criar_token_acesso, hash_senha  # noqa: E402
from app.main import app  # noqa: E402
from app.models.categoria import Categoria  # noqa: E402
from app.models.enums import PerfilUsuario  # noqa: E402
from app.models.fornecedor import Fornecedor  # noqa: E402
from app.models.responsavel import Responsavel  # noqa: E402
from app.models.setor import Setor  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema_migrado():
    command.upgrade(Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini")), "head")
    # O env.py do Alembic reconfigura o logging do processo (fileConfig); restaura o log JSON.
    configurar_logging(get_settings().log_level)
    with engine.connect() as conn:
        tabelas = conn.scalars(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        ).all()
    return ", ".join(tabelas)


@pytest.fixture(autouse=True)
def _banco_limpo(_schema_migrado: str):
    # Limpa antes (e não depois): um teste interrompido não contamina o seguinte.
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL lock_timeout = '5s'"))
        conn.execute(text(f"TRUNCATE {_schema_migrado} RESTART IDENTITY CASCADE"))  # nosec B608


@pytest.fixture
def db() -> Session:
    sessao = SessionLocal()
    try:
        yield sessao
    finally:
        sessao.close()


@pytest.fixture
def client(db: Session) -> TestClient:
    def _sobrepor_get_db():
        yield db

    app.dependency_overrides[get_db] = _sobrepor_get_db
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


def _criar_usuario(db: Session, perfil: PerfilUsuario, login: str) -> Usuario:
    usuario = Usuario(
        login=login, senha_hash=hash_senha("senha123"), nome=login.title(), perfil=perfil
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@pytest.fixture
def token_admin(db: Session) -> str:
    usuario = _criar_usuario(db, PerfilUsuario.ADMIN, "admin_teste")
    return criar_token_acesso(usuario.id, usuario.login, usuario.perfil)


@pytest.fixture
def token_operador(db: Session) -> str:
    usuario = _criar_usuario(db, PerfilUsuario.OPERADOR, "operador_teste")
    return criar_token_acesso(usuario.id, usuario.login, usuario.perfil)


@pytest.fixture
def token_auditor(db: Session) -> str:
    usuario = _criar_usuario(db, PerfilUsuario.AUDITOR, "auditor_teste")
    return criar_token_acesso(usuario.id, usuario.login, usuario.perfil)


@pytest.fixture
def token_gestor(db: Session) -> str:
    usuario = _criar_usuario(db, PerfilUsuario.GESTOR, "gestor_teste")
    return criar_token_acesso(usuario.id, usuario.login, usuario.perfil)


@pytest.fixture
def categoria(db: Session) -> Categoria:
    registro = Categoria(nome="Notebook", vida_util_meses=60, tipo_aplicavel="HARDWARE")
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


@pytest.fixture
def fornecedor(db: Session) -> Fornecedor:
    registro = Fornecedor(razao_social="Fornecedor Teste LTDA", data_source="sintetico")
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


@pytest.fixture
def setor(db: Session) -> Setor:
    registro = Setor(nome="Infraestrutura", sigla="INFRA")
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


@pytest.fixture
def responsavel(db: Session, setor: Setor) -> Responsavel:
    registro = Responsavel(nome="Carlos Menezes", matricula="M-001", setor_id=setor.id)
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


@pytest.fixture
def novo_ativo(client: TestClient, token_admin: str, categoria: Categoria, fornecedor: Fornecedor):
    """Fábrica de ativos pela API; devolve o id. HARDWARE por padrão."""
    contador = itertools.count(1)

    def _criar(
        tipo: str = "HARDWARE", data_aquisicao: str = "2025-01-10", valor: str = "1000.00", **extra
    ) -> int:
        n = next(contador)
        identificador = (
            {"numero_serie": f"SN-T{n}"}
            if tipo == "HARDWARE"
            else {"chave_licenca": f"K-T{n}-ABCD"}
        )
        resposta = client.post(
            "/api/v1/ativos",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={
                "nome": f"Ativo Teste {n}",
                "tipo": tipo,
                "categoria_id": categoria.id,
                "fornecedor_id": fornecedor.id,
                "data_aquisicao": data_aquisicao,
                "valor_compra": valor,
                **identificador,
                **extra,
            },
        )
        assert resposta.status_code == 201, resposta.text
        return resposta.json()["id"]

    return _criar


@pytest.fixture
def nova_licenca(client: TestClient, token_admin: str, fornecedor: Fornecedor):
    """Fábrica de licenças de subscrição pela API; devolve o id."""
    contador = itertools.count(1)

    def _criar(
        quantidade: int = 2, expiracao: str = "2099-12-31", inicio: str = "2025-01-01"
    ) -> int:
        n = next(contador)
        resposta = client.post(
            "/api/v1/licencas",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={
                "tipo_licenciamento": "SUBSCRICAO",
                "software": f"Software Teste {n}",
                "fornecedor_id": fornecedor.id,
                "chave_licenca": f"LIC-{n}-1234-5678",
                "quantidade_contratada": quantidade,
                "data_inicio_vigencia": inicio,
                "data_expiracao": expiracao,
                "valor_total": "100.00",
            },
        )
        assert resposta.status_code == 201, resposta.text
        return resposta.json()["id"]

    return _criar
