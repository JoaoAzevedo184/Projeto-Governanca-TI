from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_perfil
from app.models.ativo import Ativo
from app.models.baixa import BaixaAtivo
from app.models.enums import PerfilUsuario, StatusAtivo, TipoAtivo
from app.models.historico import HistoricoTransferencia
from app.models.usuario import Usuario
from app.schemas.ativo import (
    AtivoCreate,
    AtivoDados,
    AtivoResponse,
    AtivoUpdate,
    ListaAtivosResponse,
)
from app.schemas.baixa import BaixaCreate, BaixaResponse
from app.schemas.depreciacao import DepreciacaoResponse
from app.schemas.historico import VinculoCreate, VinculoResponse
from app.services import ativo_service, baixa_service, depreciacao_service, responsavel_service
from app.utils.mascaramento import chave_para_perfil

router = APIRouter(prefix="/ativos", tags=["ativos"])


def _resposta(ativo: Ativo, usuario: Usuario, *, detalhe: bool = False) -> AtivoResponse:
    dados = AtivoDados.model_validate(ativo).model_dump()
    # RI-08: a chave sai mascarada em listagens e fora do ADMIN; completa só no detalhe do ADMIN.
    dados["chave_licenca"] = chave_para_perfil(ativo.chave_licenca, usuario.perfil, detalhe=detalhe)
    return AtivoResponse(**dados, depreciacao=depreciacao_service.calcular_para_ativo(ativo))


@router.post("", response_model=AtivoResponse, status_code=201)
def criar(
    dados: AtivoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN, PerfilUsuario.OPERADOR)),
) -> AtivoResponse:
    return _resposta(ativo_service.criar_ativo(db, dados, usuario), usuario, detalhe=True)


@router.get("", response_model=ListaAtivosResponse)
def listar(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
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
        itens=[_resposta(item, usuario) for item in itens],
        pagina=pagina,
        tamanho=tamanho,
        total=total,
        total_paginas=total_paginas,
    )


@router.get("/{ativo_id}", response_model=AtivoResponse)
def obter(
    ativo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> AtivoResponse:
    return _resposta(ativo_service.obter_ativo(db, ativo_id), usuario, detalhe=True)


@router.patch("/{ativo_id}", response_model=AtivoResponse)
def atualizar(
    ativo_id: int,
    dados: AtivoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN, PerfilUsuario.OPERADOR)),
) -> AtivoResponse:
    return _resposta(
        ativo_service.atualizar_ativo(db, ativo_id, dados, usuario), usuario, detalhe=True
    )


@router.get(
    "/{ativo_id}/depreciacao",
    response_model=DepreciacaoResponse,
    dependencies=[Depends(get_current_user)],
)
def depreciacao(ativo_id: int, db: Session = Depends(get_db)) -> DepreciacaoResponse:
    return depreciacao_service.obter_depreciacao(db, ativo_id)


@router.get(
    "/{ativo_id}/historico",
    response_model=list[VinculoResponse],
    dependencies=[Depends(get_current_user)],
)
def historico(ativo_id: int, db: Session = Depends(get_db)) -> list[HistoricoTransferencia]:
    return responsavel_service.listar_historico(db, ativo_id)


@router.post("/{ativo_id}/responsavel", response_model=VinculoResponse, status_code=201)
def atribuir_responsavel(
    ativo_id: int,
    dados: VinculoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN, PerfilUsuario.OPERADOR)),
) -> HistoricoTransferencia:
    return responsavel_service.atribuir_responsavel(db, ativo_id, dados, usuario)


@router.post("/{ativo_id}/baixa", response_model=BaixaResponse, status_code=201)
def registrar_baixa(
    ativo_id: int,
    dados: BaixaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN, PerfilUsuario.OPERADOR)),
) -> BaixaAtivo:
    return baixa_service.registrar_baixa(db, ativo_id, dados, usuario)
