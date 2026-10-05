from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_perfil
from app.models.enums import PerfilUsuario, StatusRecomendacao
from app.models.recomendacao import Recomendacao
from app.models.usuario import Usuario
from app.schemas.recomendacao import (
    ListaRecomendacoesResponse,
    RecomendacaoCreate,
    RecomendacaoResponse,
)
from app.services import recomendacao_service

router = APIRouter(prefix="/recomendacoes", tags=["recomendacoes"])


@router.post("", response_model=RecomendacaoResponse, status_code=201)
def criar(
    dados: RecomendacaoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GESTOR)),
) -> Recomendacao:
    return recomendacao_service.criar_recomendacao(db, dados, usuario)


@router.get("", response_model=ListaRecomendacoesResponse)
def listar(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
    status: StatusRecomendacao | None = None,
    pagina: int = Query(default=1, ge=1),
    tamanho: int = Query(default=20, ge=1, le=100),
) -> ListaRecomendacoesResponse:
    itens, total = recomendacao_service.listar_recomendacoes(
        db, status=status, pagina=pagina, tamanho=tamanho
    )
    return ListaRecomendacoesResponse(
        itens=[RecomendacaoResponse.model_validate(i) for i in itens],
        pagina=pagina,
        tamanho=tamanho,
        total=total,
        total_paginas=ceil(total / tamanho) if total else 0,
    )


@router.get("/{recomendacao_id}", response_model=RecomendacaoResponse)
def obter(
    recomendacao_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
) -> Recomendacao:
    return recomendacao_service.obter_recomendacao(db, recomendacao_id)
