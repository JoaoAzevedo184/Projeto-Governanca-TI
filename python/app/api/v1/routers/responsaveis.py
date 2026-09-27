from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_perfil
from app.models.enums import PerfilUsuario
from app.models.responsavel import Responsavel
from app.models.usuario import Usuario
from app.schemas.responsavel import ResponsavelCreate, ResponsavelResponse
from app.services.responsavel_service import criar_responsavel

router = APIRouter(prefix="/responsaveis", tags=["responsaveis"])


@router.get("", response_model=list[ResponsavelResponse], dependencies=[Depends(get_current_user)])
def listar(db: Session = Depends(get_db)) -> list[Responsavel]:
    return list(db.query(Responsavel).order_by(Responsavel.nome))


@router.post("", response_model=ResponsavelResponse, status_code=201)
def criar(
    dados: ResponsavelCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN, PerfilUsuario.OPERADOR)),
) -> Responsavel:
    return criar_responsavel(db, dados, usuario)
