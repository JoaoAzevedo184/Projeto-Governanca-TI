from pydantic import BaseModel

from app.models.enums import PerfilUsuario


class LoginRequest(BaseModel):
    login: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioResponse(BaseModel):
    id: int
    login: str
    nome: str
    perfil: PerfilUsuario
    ativo: bool

    model_config = {"from_attributes": True}
