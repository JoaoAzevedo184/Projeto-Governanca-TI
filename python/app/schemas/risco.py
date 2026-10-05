from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import CategoriaRisco, ClassificacaoRisco, RespostaRisco, StatusRisco


class RiscoCreate(BaseModel):
    """Corpo de `POST /riscos` (FR-012). `score` e `classificacao` não se informam."""

    titulo: str = Field(min_length=3, max_length=160)
    descricao: str | None = Field(default=None, max_length=1000)
    categoria: CategoriaRisco
    probabilidade: int = Field(ge=1, le=5)
    impacto: int = Field(ge=1, le=5)
    resposta: RespostaRisco
    responsavel_id: int | None = None
    status: StatusRisco = StatusRisco.ABERTO
    gatilho: str | None = Field(default=None, max_length=255)
    data_revisao: date | None = None


class RiscoUpdate(BaseModel):
    """Corpo de `PATCH /riscos/{id}`: só o que muda. O `score` acompanha sozinho."""

    titulo: str | None = Field(default=None, min_length=3, max_length=160)
    descricao: str | None = Field(default=None, max_length=1000)
    categoria: CategoriaRisco | None = None
    probabilidade: int | None = Field(default=None, ge=1, le=5)
    impacto: int | None = Field(default=None, ge=1, le=5)
    resposta: RespostaRisco | None = None
    responsavel_id: int | None = None
    status: StatusRisco | None = None
    gatilho: str | None = Field(default=None, max_length=255)
    data_revisao: date | None = None


class RiscoResponse(BaseModel):
    id: int
    titulo: str
    descricao: str | None
    categoria: CategoriaRisco
    probabilidade: int
    impacto: int
    score: int = Field(description="probabilidade × impacto, de 1 a 25 (AC-050).")
    classificacao: ClassificacaoRisco = Field(
        description="Baixo 1–4, médio 5–9, alto 10–14, crítico 15–25."
    )
    resposta: RespostaRisco
    responsavel_id: int | None
    status: StatusRisco
    gatilho: str | None
    data_revisao: date | None
    data_source: str
    criado_em: datetime
    atualizado_em: datetime


class ListaRiscosResponse(BaseModel):
    itens: list[RiscoResponse]
    pagina: int
    tamanho: int
    total: int
    total_paginas: int
