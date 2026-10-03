"""Endpoints técnicos, fora de `/api/v1` e públicos (contrato §6.8): `/health` e `/metrics`."""

from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.saude import SaudeResponse
from app.services import observabilidade_service

router = APIRouter(tags=["tecnico"])


@router.get("/health", response_model=SaudeResponse)
def health(response: Response, db: Session = Depends(get_db)) -> SaudeResponse:
    saude = observabilidade_service.estado_saude(db)
    if saude.status != "UP":
        response.status_code = 503
    return saude


@router.get("/metrics", include_in_schema=False)
def metrics(db: Session = Depends(get_db)) -> Response:
    observabilidade_service.atualizar_gauges(db)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
