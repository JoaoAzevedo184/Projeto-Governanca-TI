from math import ceil

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_perfil
from app.models.enums import PerfilUsuario, TipoLicenciamento
from app.models.licenca import LicencaVinculo
from app.models.usuario import Usuario
from app.schemas.licenca import (
    LicencaCreate,
    LicencaResponse,
    LicencaUpdate,
    ListaLicencasResponse,
    VinculoLicencaCreate,
    VinculoLicencaResponse,
)
from app.services import licenca_service

router = APIRouter(prefix="/licencas", tags=["licencas"])

# FR-015: Licenças = ADMIN (CRUD) · OPERADOR (Ler, Editar) · GESTOR e AUDITOR (Ler).
_EDITAM = (PerfilUsuario.ADMIN, PerfilUsuario.OPERADOR)


@router.post("", response_model=LicencaResponse, status_code=201)
def criar(
    dados: LicencaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN)),
) -> LicencaResponse:
    return licenca_service.criar_licenca(db, dados, usuario)


@router.get("", response_model=ListaLicencasResponse)
def listar(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    tipo_licenciamento: TipoLicenciamento | None = None,
    fornecedor_id: int | None = None,
    pagina: int = Query(default=1, ge=1),
    tamanho: int = Query(default=20, ge=1, le=100),
) -> ListaLicencasResponse:
    itens, total = licenca_service.listar_licencas(
        db,
        usuario,
        tipo_licenciamento=tipo_licenciamento,
        fornecedor_id=fornecedor_id,
        pagina=pagina,
        tamanho=tamanho,
    )
    return ListaLicencasResponse(
        itens=itens,
        pagina=pagina,
        tamanho=tamanho,
        total=total,
        total_paginas=ceil(total / tamanho) if total else 0,
    )


@router.get("/{licenca_id}", response_model=LicencaResponse)
def obter(
    licenca_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> LicencaResponse:
    return licenca_service.obter_licenca(db, licenca_id, usuario)


@router.patch("/{licenca_id}", response_model=LicencaResponse)
def atualizar(
    licenca_id: int,
    dados: LicencaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(*_EDITAM)),
) -> LicencaResponse:
    return licenca_service.atualizar_licenca(db, licenca_id, dados, usuario)


@router.get(
    "/{licenca_id}/vinculos",
    response_model=list[VinculoLicencaResponse],
    dependencies=[Depends(get_current_user)],
)
def listar_vinculos(licenca_id: int, db: Session = Depends(get_db)) -> list[LicencaVinculo]:
    return licenca_service.listar_vinculos(db, licenca_id)


@router.post("/{licenca_id}/vinculos", response_model=VinculoLicencaResponse, status_code=201)
def vincular(
    licenca_id: int,
    dados: VinculoLicencaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(*_EDITAM)),
) -> LicencaVinculo:
    return licenca_service.vincular(db, licenca_id, dados, usuario)


@router.delete("/{licenca_id}/vinculos/{ativo_id}", status_code=204)
def desvincular(
    licenca_id: int,
    ativo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(*_EDITAM)),
) -> Response:
    licenca_service.desvincular(db, licenca_id, ativo_id, usuario)
    return Response(status_code=204)
