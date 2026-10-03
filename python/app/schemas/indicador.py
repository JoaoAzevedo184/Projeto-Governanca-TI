from datetime import date

from pydantic import BaseModel, Field


class IndicadorResponse(BaseModel):
    codigo: str
    nome: str
    valor: int | float | str | None = Field(
        description="Valor monetário como string decimal; percentual e contagem como número. "
        "Nulo quando a amostra é vazia."
    )
    unidade: str
    formula: str = Field(description="A fórmula aplicada (AC-047).")
    amostra: int = Field(description="Tamanho da amostra usada (AC-047).")
    meta: float | None = None
    sentido_meta: str | None = Field(default=None, description="`>=` ou `<=`.")
    atende_meta: bool | None = None
    detalhe: dict[str, int] | None = Field(
        default=None, description="Desdobramento, nos indicadores de distribuição."
    )


class IndicadoresResponse(BaseModel):
    data_referencia: date
    filtros_aplicados: dict[str, int | date | None]
    indicadores: list[IndicadorResponse]
