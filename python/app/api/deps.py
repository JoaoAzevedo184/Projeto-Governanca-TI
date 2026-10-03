from collections.abc import Callable

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NaoAutenticadoError, PermissaoNegadaError
from app.core.security import decodificar_token
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

__all__ = ["get_db", "get_current_user", "require_perfil"]


def get_current_user(
    request: Request,
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    payload = decodificar_token(token)
    usuario = db.get(Usuario, int(payload["sub"]))
    if usuario is None or not usuario.ativo:
        raise NaoAutenticadoError("Usuário do token não existe mais ou está inativo.")
    request.state.usuario_id = usuario.id  # para o log de acesso e o de recusa
    return usuario


def require_perfil(*perfis: PerfilUsuario) -> Callable[[Usuario], Usuario]:
    def _verificar(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.perfil not in perfis:
            raise PermissaoNegadaError(perfil=str(usuario.perfil))
        return usuario

    return _verificar
