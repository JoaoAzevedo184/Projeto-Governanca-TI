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

    Usado nas unicidades de cadastro (categoria.nome, fornecedor.cnpj, setor.nome,
    responsavel.matricula), que não têm BR numerado — ver nota no início do §3 de
    docs/modelo-de-dados/dicionario-de-dados.md. O conflito de BR-007 tem tratamento próprio,
    com savepoint e auditoria, em responsavel_service.atribuir_responsavel.
    """
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise RegraNegocioError(mensagem) from exc
