from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_perfil
from app.models.enums import PerfilUsuario
from app.models.setor import Setor
from app.models.usuario import Usuario
from app.schemas.setor import SetorCreate, SetorResponse
from app.services.setor_service import criar_setor

router = APIRouter(prefix="/setores", tags=["setores"])


@router.get("", response_model=list[SetorResponse], dependencies=[Depends(get_current_user)])
def listar(db: Session = Depends(get_db)) -> list[Setor]:
    return list(db.query(Setor).order_by(Setor.nome))


@router.post("", response_model=SetorResponse, status_code=201)
def criar(
    dados: SetorCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN)),
) -> Setor:
    return criar_setor(db, dados, usuario)
