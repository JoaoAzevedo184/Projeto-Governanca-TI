from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import EVIDENCIAS_SEM_REFERENCIA, StatusRecomendacao, TipoEvidencia
from app.utils.datas import hoje


class EvidenciaCreate(BaseModel):
    """O que sustenta a recomendação (FR-013). `RISCO`, `ATIVO`, `LICENCA` e `SCORECARD` (este com o
    id do fornecedor avaliado) exigem `referencia_id` de um registro existente; `INDICADOR`,
    `CENARIO` e `PREMISSA` não têm registro (são derivados ou declarados) e exigem `descricao`."""

    tipo: TipoEvidencia
    referencia_id: int | None = Field(default=None, gt=0)
    descricao: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _validar_por_tipo(self) -> "EvidenciaCreate":
        if self.tipo in EVIDENCIAS_SEM_REFERENCIA:
            if self.referencia_id is not None:
                raise ValueError(f"{self.tipo.value} não tem registro: omita referencia_id.")
            if len((self.descricao or "").strip()) < 3:
                raise ValueError(f"{self.tipo.value} exige descricao (valor ou premissa).")
        elif self.referencia_id is None:
            raise ValueError(f"{self.tipo.value} exige referencia_id.")
        return self


class RecomendacaoCreate(BaseModel):
    """Corpo de `POST /recomendacoes` (FR-013).

    `evidencias` é opcional no schema de propósito: a ausência (lista vazia) é recusada pelo
    serviço com 409 e `regra = BR-027`, registrada na auditoria (NFR-AUD-05, AC-051).
    O sistema só registra: a decisão é de quem assina (`responsavel_id`).
    """

    titulo: str = Field(min_length=3, max_length=160)
    contexto: str = Field(min_length=1, max_length=2000)
    recomendacao: str = Field(min_length=1, max_length=2000)
    alternativas: str | None = Field(default=None, max_length=2000)
    responsavel_id: int
    data: date | None = Field(default=None, description="Data da decisão. Padrão: hoje.")
    status: StatusRecomendacao = StatusRecomendacao.PROPOSTA
    evidencias: list[EvidenciaCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validar_data_nao_futura(self) -> "RecomendacaoCreate":
        if self.data is not None and self.data > hoje():
            raise ValueError("data não pode ser posterior à data corrente.")
        return self


class EvidenciaResponse(BaseModel):
    id: int
    tipo: TipoEvidencia
    referencia_id: int | None
    descricao: str | None

    model_config = {"from_attributes": True}


class RecomendacaoResponse(BaseModel):
    id: int
    titulo: str
    contexto: str
    recomendacao: str
    alternativas: str | None
    responsavel_id: int
    data: date
    status: StatusRecomendacao
    data_source: str
    criado_em: datetime
    evidencias: list[EvidenciaResponse]

    model_config = {"from_attributes": True}


class ListaRecomendacoesResponse(BaseModel):
    itens: list[RecomendacaoResponse]
    pagina: int
    tamanho: int
    total: int
    total_paginas: int
