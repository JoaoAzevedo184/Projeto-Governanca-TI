from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.utils.datas import hoje


class VinculoCreate(BaseModel):
    """Corpo de `POST /ativos/{id}/responsavel` — atribuição inicial ou transferência (FR-002)."""

    responsavel_id: int
    setor_id: int
    data_inicio: date
    motivo: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _validar_data_inicio_nao_futura(self) -> "VinculoCreate":
        if self.data_inicio > hoje():
            raise ValueError("data_inicio não pode ser posterior à data corrente (FR-002).")
        return self


class VinculoResponse(BaseModel):
    id: int
    ativo_id: int
    responsavel_id: int
    setor_id: int
    data_inicio: date
    data_fim: date | None
    motivo: str | None
    registrado_por_id: int
    data_source: str
    criado_em: datetime

    model_config = {"from_attributes": True}
