from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_perfil
from app.models.enums import CategoriaRisco, ClassificacaoRisco, PerfilUsuario, StatusRisco
from app.models.usuario import Usuario
from app.schemas.risco import ListaRiscosResponse, RiscoCreate, RiscoResponse, RiscoUpdate
from app.services import risco_service

router = APIRouter(prefix="/riscos", tags=["riscos"])

# Contrato §6.7: leitura para todos os perfis (FR-015), escrita só para ADMIN e GESTOR.
_ESCREVEM = (PerfilUsuario.ADMIN, PerfilUsuario.GESTOR)


@router.post("", response_model=RiscoResponse, status_code=201)
def criar(
    dados: RiscoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(*_ESCREVEM)),
) -> RiscoResponse:
    return risco_service.criar_risco(db, dados, usuario)


@router.get("", response_model=ListaRiscosResponse)
def listar(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
    categoria: CategoriaRisco | None = None,
    status: StatusRisco | None = None,
    classificacao: ClassificacaoRisco | None = None,
    pagina: int = Query(default=1, ge=1),
    tamanho: int = Query(default=20, ge=1, le=100),
) -> ListaRiscosResponse:
    itens, total = risco_service.listar_riscos(
        db,
        categoria=categoria,
        status=status,
        classificacao=classificacao,
        pagina=pagina,
        tamanho=tamanho,
    )
    return ListaRiscosResponse(
        itens=itens,
        pagina=pagina,
        tamanho=tamanho,
        total=total,
        total_paginas=ceil(total / tamanho) if total else 0,
    )


@router.get("/{risco_id}", response_model=RiscoResponse)
def obter(
    risco_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
) -> RiscoResponse:
    return risco_service.obter_risco(db, risco_id)


@router.patch("/{risco_id}", response_model=RiscoResponse)
def atualizar(
    risco_id: int,
    dados: RiscoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(*_ESCREVEM)),
) -> RiscoResponse:
    return risco_service.atualizar_risco(db, risco_id, dados, usuario)
