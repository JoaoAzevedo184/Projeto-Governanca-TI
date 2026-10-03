from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.indicador import IndicadoresResponse
from app.services import indicador_service

router = APIRouter(prefix="/indicadores", tags=["indicadores"])


@router.get("", response_model=IndicadoresResponse)
def indicadores(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
    categoria_id: int | None = None,
    setor_id: int | None = None,
    fornecedor_id: int | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> IndicadoresResponse:
    return indicador_service.calcular_indicadores(
        db,
        categoria_id=categoria_id,
        setor_id=setor_id,
        fornecedor_id=fornecedor_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
