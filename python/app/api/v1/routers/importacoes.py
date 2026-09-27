from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_perfil
from app.core.exceptions import RecursoNaoEncontradoError
from app.models.enums import PerfilUsuario
from app.models.importacao import ErroImportacao, LoteImportacao
from app.models.usuario import Usuario
from app.schemas.importacao import ErroImportacaoResponse, ImportacaoResumo, LoteImportacaoResponse
from app.services.importacao_service import processar_importacao

router = APIRouter(prefix="/importacoes", tags=["importacoes"])

_PERFIS_LEITURA = (
    PerfilUsuario.ADMIN,
    PerfilUsuario.OPERADOR,
    PerfilUsuario.GESTOR,
    PerfilUsuario.AUDITOR,
)


@router.post("", response_model=ImportacaoResumo, status_code=202)
async def importar(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN)),
) -> ImportacaoResumo:
    conteudo = await arquivo.read()
    lote = processar_importacao(db, arquivo.filename or "arquivo", conteudo, usuario)
    return ImportacaoResumo(
        lote_id=lote.id,
        nome_arquivo=lote.nome_arquivo,
        total_processado=lote.total_processado,
        total_aceito=lote.total_aceito,
        total_rejeitado=lote.total_rejeitado,
        erros_url=f"/api/v1/importacoes/{lote.id}/erros",
    )


@router.get(
    "",
    response_model=list[LoteImportacaoResponse],
    dependencies=[Depends(require_perfil(*_PERFIS_LEITURA))],
)
def listar(db: Session = Depends(get_db)) -> list[LoteImportacao]:
    return list(db.query(LoteImportacao).order_by(LoteImportacao.id.desc()))


@router.get(
    "/{lote_id}",
    response_model=LoteImportacaoResponse,
    dependencies=[Depends(require_perfil(*_PERFIS_LEITURA))],
)
def obter(lote_id: int, db: Session = Depends(get_db)) -> LoteImportacao:
    lote = db.get(LoteImportacao, lote_id)
    if lote is None:
        raise RecursoNaoEncontradoError(f"Lote {lote_id} não encontrado.")
    return lote


@router.get(
    "/{lote_id}/erros",
    response_model=list[ErroImportacaoResponse],
    dependencies=[Depends(require_perfil(*_PERFIS_LEITURA))],
)
def erros(lote_id: int, db: Session = Depends(get_db)) -> list[ErroImportacao]:
    return list(
        db.query(ErroImportacao)
        .filter(ErroImportacao.lote_id == lote_id)
        .order_by(ErroImportacao.numero_linha)
    )
