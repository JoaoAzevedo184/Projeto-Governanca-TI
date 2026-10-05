from typing import Any

from pydantic import BaseModel, Field


class ErroResponse(BaseModel):
    """Corpo de erro único da API, inspirado na RFC 7807 (docs/spec/padrao-de-erros.md)."""

    tipo: str = Field(description="Identificador do tipo de erro, ex.: /erros/regra-de-negocio.")
    titulo: str
    status: int
    detalhe: str
    instancia: str = Field(description="Caminho da requisição.")
    regra: str | None = Field(
        description="BR da regra de negócio violada (nas recusas 409) ou FR-015 (403)."
    )
    erros: list[Any] = Field(description="Detalhe por campo, nos erros de validação (422).")
