from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import NaoAutenticadoError

settings = get_settings()
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    return _pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return _pwd_context.verify(senha, senha_hash)


def criar_token_acesso(usuario_id: int, login: str, perfil: str) -> str:
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "login": login,
        "perfil": perfil,
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise NaoAutenticadoError("Token JWT ausente, expirado ou inválido.") from exc
