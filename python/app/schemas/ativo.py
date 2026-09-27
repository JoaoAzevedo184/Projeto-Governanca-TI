from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import StatusAtivo, TipoAtivo


class AtivoCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    tipo: TipoAtivo
    categoria_id: int
    fornecedor_id: int
    numero_serie: str | None = Field(default=None, max_length=80)
    chave_licenca: str | None = Field(default=None, max_length=200)
    data_aquisicao: date
    valor_compra: Decimal = Field(gt=0)
    vida_util_meses: int | None = Field(default=None, gt=0)
    localizacao: str | None = Field(default=None, max_length=120)
    observacoes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _validar_identificador_por_tipo(self) -> "AtivoCreate":
        if self.tipo == TipoAtivo.HARDWARE and not self.numero_serie:
            raise ValueError("numero_serie é obrigatório para ativos do tipo HARDWARE (BR-002).")
        if self.tipo == TipoAtivo.SOFTWARE and not self.chave_licenca:
            raise ValueError("chave_licenca é obrigatória para ativos do tipo SOFTWARE (BR-002).")
        return self

    @model_validator(mode="after")
    def _validar_data_aquisicao_nao_futura(self) -> "AtivoCreate":
        if self.data_aquisicao > date.today():
            raise ValueError("data_aquisicao não pode ser posterior à data corrente (BR-003).")
        return self


class AtivoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=120)
    categoria_id: int | None = None
    fornecedor_id: int | None = None
    vida_util_meses: int | None = Field(default=None, gt=0)
    localizacao: str | None = Field(default=None, max_length=120)
    observacoes: str | None = Field(default=None, max_length=500)


class AtivoResponse(BaseModel):
    id: int
    nome: str
    tipo: TipoAtivo
    categoria_id: int
    fornecedor_id: int
    numero_serie: str | None
    chave_licenca: str | None
    data_aquisicao: date
    valor_compra: Decimal
    vida_util_meses: int
    status: StatusAtivo
    localizacao: str | None
    observacoes: str | None
    data_source: str
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class ListaAtivosResponse(BaseModel):
    itens: list[AtivoResponse]
    pagina: int
    tamanho: int
    total: int
    total_paginas: int
