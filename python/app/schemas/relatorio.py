from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import StatusAtivo, TipoAtivo


class LinhaInventario(BaseModel):
    id: int
    nome: str
    tipo: TipoAtivo
    categoria: str
    identificador: str | None  # número de série, ou a chave de licença mascarada (RI-08)
    responsavel: str | None
    setor: str | None
    status: StatusAtivo
    data_aquisicao: date
    valor_compra: Decimal
    depreciacao_acumulada: Decimal
    percentual_depreciado: Decimal
    valor_residual: Decimal
    fornecedor: str


class TotaisInventario(BaseModel):
    """Totalizadores sobre todo o resultado filtrado, não só a página (FR-006)."""

    quantidade: int
    valor_compra: Decimal
    valor_residual: Decimal


class InventarioResponse(BaseModel):
    itens: list[LinhaInventario]
    pagina: int
    tamanho: int
    total: int
    total_paginas: int
    totais: TotaisInventario
