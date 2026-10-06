from collections.abc import Callable

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NaoAutenticadoError, PermissaoNegadaError
from app.core.security import decodificar_token
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario


class EsquemaBearer(HTTPBearer):
    """HTTP Bearer no OpenAPI (o Swagger mostra um campo de token no Authorize), com as mesmas
    respostas de antes: o `HTTPBearer` do FastAPI responde 403 sem credenciais, e o projeto
    sempre respondeu 401 no formato de erro próprio."""

    async def __call__(self, request: Request) -> str:  # type: ignore[override]
        autorizacao = request.headers.get("Authorization")
        esquema, token = get_authorization_scheme_param(autorizacao)
        if not autorizacao or esquema.lower() != "bearer":
            raise HTTPException(
                status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"}
            )
        return token


_esquema_bearer = EsquemaBearer(
    scheme_name="HTTPBearer",
    bearerFormat="JWT",
    description="Token devolvido por `POST /api/v1/auth/login`: cole só o `access_token`.",
)

__all__ = ["get_db", "get_current_user", "require_perfil"]


def get_current_user(
    request: Request,
    token: str = Depends(_esquema_bearer),
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
