import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.security import criar_token_acesso, hash_senha
from app.main import app
from app.models.base import Base
from app.models.categoria import Categoria
from app.models.enums import PerfilUsuario
from app.models.fornecedor import Fornecedor
from app.models.usuario import Usuario

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _banco_limpo():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def db() -> Session:
    sessao = _SessionLocal()
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
