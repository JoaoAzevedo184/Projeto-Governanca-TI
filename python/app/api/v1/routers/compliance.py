from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.compliance import AlertasResponse
from app.services import compliance_service

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/alertas", response_model=AlertasResponse)
def alertas(
    db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
) -> AlertasResponse:
    # FR-015: Relatórios = Ler para os quatro perfis.
    return compliance_service.listar_alertas(db)
