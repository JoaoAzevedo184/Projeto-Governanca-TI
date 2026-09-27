from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_perfil
from app.models.ativo import Ativo
from app.models.enums import PerfilUsuario, StatusAtivo, TipoAtivo
from app.models.usuario import Usuario
from app.schemas.ativo import AtivoCreate, AtivoResponse, AtivoUpdate, ListaAtivosResponse
from app.services import ativo_service

router = APIRouter(prefix="/ativos", tags=["ativos"])


@router.post("", response_model=AtivoResponse, status_code=201)
def criar(
    dados: AtivoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN, PerfilUsuario.OPERADOR)),
) -> Ativo:
    return ativo_service.criar_ativo(db, dados, usuario)


@router.get("", response_model=ListaAtivosResponse, dependencies=[Depends(get_current_user)])
def listar(
    db: Session = Depends(get_db),
    status: StatusAtivo | None = None,
    tipo: TipoAtivo | None = None,
    categoria_id: int | None = None,
    fornecedor_id: int | None = None,
    busca: str | None = None,
    pagina: int = Query(default=1, ge=1),
    tamanho: int = Query(default=20, ge=1, le=100),
    ordenar_por: str = "id",
    direcao: str = "asc",
) -> ListaAtivosResponse:
    itens, total = ativo_service.listar_ativos(
        db,
        status=status,
        tipo=tipo,
        categoria_id=categoria_id,
        fornecedor_id=fornecedor_id,
        busca=busca,
        pagina=pagina,
        tamanho=tamanho,
        ordenar_por=ordenar_por,
        direcao=direcao,
    )
    total_paginas = ceil(total / tamanho) if total else 0
    return ListaAtivosResponse(
        itens=[AtivoResponse.model_validate(item) for item in itens],
        pagina=pagina,
        tamanho=tamanho,
        total=total,
        total_paginas=total_paginas,
    )


@router.get("/{ativo_id}", response_model=AtivoResponse, dependencies=[Depends(get_current_user)])
def obter(ativo_id: int, db: Session = Depends(get_db)) -> Ativo:
    return ativo_service.obter_ativo(db, ativo_id)


@router.patch("/{ativo_id}", response_model=AtivoResponse)
def atualizar(
    ativo_id: int,
    dados: AtivoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN, PerfilUsuario.OPERADOR)),
) -> Ativo:
    return ativo_service.atualizar_ativo(db, ativo_id, dados, usuario)
