from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_perfil
from app.models.enums import PerfilUsuario
from app.models.fornecedor import Fornecedor
from app.models.usuario import Usuario
from app.schemas.fornecedor import FornecedorCreate, FornecedorResponse
from app.services.fornecedor_service import criar_fornecedor

router = APIRouter(prefix="/fornecedores", tags=["fornecedores"])


@router.get("", response_model=list[FornecedorResponse], dependencies=[Depends(get_current_user)])
def listar(db: Session = Depends(get_db)) -> list[Fornecedor]:
    return list(db.query(Fornecedor).order_by(Fornecedor.razao_social))


@router.post("", response_model=FornecedorResponse, status_code=201)
def criar(
    dados: FornecedorCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN)),
) -> Fornecedor:
    return criar_fornecedor(db, dados, usuario)
