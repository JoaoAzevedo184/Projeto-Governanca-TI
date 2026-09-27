from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import NaoAutenticadoError
from app.core.security import criar_token_acesso, verificar_senha
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, TokenResponse, UsuarioResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    usuario = db.scalar(select(Usuario).where(Usuario.login == dados.login))
    if usuario is None or not usuario.ativo or not verificar_senha(dados.senha, usuario.senha_hash):
        raise NaoAutenticadoError("Login ou senha inválidos.")
    token = criar_token_acesso(usuario.id, usuario.login, usuario.perfil)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioResponse)
def me(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    return usuario
