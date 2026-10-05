from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_perfil
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario
from app.schemas.cenario import CompararCenariosCreate, CompararCenariosResponse
from app.services import cenario_service

router = APIRouter(prefix="/cenarios", tags=["cenarios"])


@router.post("/comparar", response_model=CompararCenariosResponse)
def comparar(
    dados: CompararCenariosCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GESTOR)),
) -> CompararCenariosResponse:
    return cenario_service.comparar_cenarios(db, dados)
