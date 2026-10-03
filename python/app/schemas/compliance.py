from datetime import date

from pydantic import BaseModel, Field


class AlertaResponse(BaseModel):
    """Alerta derivado do estado atual, nunca persistido (FR-007)."""

    codigo: str = Field(description="CP-01 a CP-04.")
    severidade: str = Field(description="CRITICO, ALTO, MEDIO ou BAIXO.")
    regra: str = Field(description="A regra aplicada, legível (AC-042).")
    mensagem: str
    entidade: str = Field(description="`licenca` ou `ativo`: o registro de origem (AC-041).")
    entidade_id: int
    recurso: str = Field(description="Nome do software ou do ativo.")
    link: str = Field(description="Rota do registro de origem.")


class GrupoAlertas(BaseModel):
    severidade: str
    total: int
    alertas: list[AlertaResponse]


class AlertasResponse(BaseModel):
    data_referencia: date
    total: int
    por_severidade: dict[str, int]
    grupos: list[GrupoAlertas] = Field(
        description="Só as severidades com alerta, da mais crítica para a menos (AC-040)."
    )
