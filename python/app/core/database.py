from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.exceptions import RegraNegocioError

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def flush_ou_conflito(db: Session, mensagem: str) -> None:
    """`db.flush()` convertendo violação de UNIQUE/CHECK em 409 (padrão RFC 7807 do SPEC).

    Sem BR numerado para as unicidades de cadastro (categoria.nome, fornecedor.cnpj,
    setor.nome, responsavel.matricula) — ver observação em docs/ROADMAP.md — por isso
    nenhuma `regra` é anexada aqui.
    """
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise RegraNegocioError(mensagem) from exc
