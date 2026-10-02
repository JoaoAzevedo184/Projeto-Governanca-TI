from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import DestinacaoBaixa, MotivoBaixa


class BaixaCreate(BaseModel):
    """Corpo de `POST /ativos/{id}/baixa` (FR-005, contrato §6.3).

    `destinacao` e a justificativa de `OUTRO` são opcionais no schema de propósito: a ausência é
    recusada pelo serviço com 409 e `regra` (BR-026, BR-023), registrada na auditoria
    (NFR-AUD-05). O mesmo vale para a data (BR-022).
    """

    motivo: MotivoBaixa
    justificativa: str | None = Field(default=None, max_length=500)
    data_baixa: date
    destinacao: DestinacaoBaixa | None = None


class BaixaResponse(BaseModel):
    id: int
    ativo_id: int
    motivo: MotivoBaixa
    justificativa: str | None
    data_baixa: date
    destinacao: DestinacaoBaixa
    valor_residual_baixa: Decimal
    registrado_por_id: int
    data_source: str
    criado_em: datetime

    model_config = {"from_attributes": True}
