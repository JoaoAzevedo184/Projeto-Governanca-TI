from datetime import date
from decimal import Decimal
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.enums import StatusAtivo, TipoAtivo
from app.models.usuario import Usuario
from app.schemas.compliance import AlertasResponse
from app.schemas.relatorio import InventarioResponse
from app.services import compliance_service, relatorio_service
from app.services.relatorio_service import FiltrosInventario

router = APIRouter(prefix="/relatorios", tags=["relatorios"])

Formato = Literal["json", "csv", "xlsx"]

# Em `csv` e `xlsx` a resposta é um arquivo, não JSON (contrato §6.5).
_ARQUIVOS: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "JSON, ou arquivo CSV/XLSX conforme `formato`.",
        "content": {
            "text/csv": {},
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
        },
    }
}


def _arquivo(conteudo: bytes, media_type: str, nome: str, formato: str) -> Response:
    return Response(
        conteudo,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{nome}.{formato}"'},
    )


@router.get("/inventario", response_model=InventarioResponse, responses=_ARQUIVOS)
def inventario(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    formato: Formato = "json",
    status: list[StatusAtivo] | None = Query(default=None),
    tipo: list[TipoAtivo] | None = Query(default=None),
    categoria_id: list[int] | None = Query(default=None),
    fornecedor_id: list[int] | None = Query(default=None),
    responsavel_id: int | None = None,
    valor_depreciado_min: Decimal | None = None,
    valor_depreciado_max: Decimal | None = None,
    percentual_depreciado_min: Decimal | None = None,
    percentual_depreciado_max: Decimal | None = None,
    aquisicao_de: date | None = None,
    aquisicao_ate: date | None = None,
    fim_vida_util: bool | None = None,
    pagina: int = Query(default=1, ge=1),
    tamanho: int = Query(default=20, ge=1, le=100),
):
    filtros = FiltrosInventario(
        status=status,
        tipo=tipo,
        categoria_id=categoria_id,
        fornecedor_id=fornecedor_id,
        responsavel_id=responsavel_id,
        valor_depreciado_min=valor_depreciado_min,
        valor_depreciado_max=valor_depreciado_max,
        percentual_depreciado_min=percentual_depreciado_min,
        percentual_depreciado_max=percentual_depreciado_max,
        aquisicao_de=aquisicao_de,
        aquisicao_ate=aquisicao_ate,
        fim_vida_util=fim_vida_util,
    )
    if formato == "json":
        return relatorio_service.inventario(db, usuario, filtros, pagina=pagina, tamanho=tamanho)
    conteudo, media_type = relatorio_service.exportar_inventario(db, usuario, formato, filtros)
    return _arquivo(conteudo, media_type, "inventario", formato)


@router.get("/conformidade", response_model=AlertasResponse, responses=_ARQUIVOS)
def conformidade(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    formato: Formato = "json",
):
    if formato == "json":
        return compliance_service.listar_alertas(db)
    conteudo, media_type = relatorio_service.exportar_conformidade(db, usuario, formato)
    return _arquivo(conteudo, media_type, "conformidade", formato)
