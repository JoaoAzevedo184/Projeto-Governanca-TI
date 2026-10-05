from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from app.models.enums import NomeCenario

Dinheiro = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]


class EntradaCenarioCreate(BaseModel):
    nome: NomeCenario
    capex: Dinheiro = Field(description="Investimento inicial, em reais.")
    opex_anual: Dinheiro = Field(description="Custo recorrente por ano, em reais.")
    riscos_ids: list[int] = Field(
        default_factory=list, description="Riscos vinculados ao cenário: o score soma os deles."
    )


class CompararCenariosCreate(BaseModel):
    """Corpo de `POST /cenarios/comparar` (FR-010). Entre 2 e 3 cenários, sem nome repetido."""

    cenarios: list[EntradaCenarioCreate] = Field(min_length=2, max_length=3)
    quantidade_ativos: int | None = Field(
        default=None,
        gt=0,
        description="Ativos do parque no cálculo por ativo/ano. Padrão: ativos não baixados.",
    )

    @model_validator(mode="after")
    def _validar_unicidade(self) -> "CompararCenariosCreate":
        nomes = [c.nome for c in self.cenarios]
        if len(set(nomes)) != len(nomes):
            raise ValueError("Há cenário repetido.")
        for cenario in self.cenarios:
            if len(set(cenario.riscos_ids)) != len(cenario.riscos_ids):
                raise ValueError(f"Cenário {cenario.nome.value}: há risco repetido.")
        return self


class CenarioResultado(BaseModel):
    nome: NomeCenario
    capex: Decimal
    opex_anual: Decimal
    tco_5_anos: Decimal = Field(description="capex + opex_anual × 5.")
    custo_por_ativo_ano: Decimal | None = Field(
        description="tco ÷ (ativos × 5); nulo se não há ativos."
    )
    economia_vs_baseline: Decimal = Field(description="tco do baseline − tco do cenário.")
    score_risco: int = Field(description="Soma dos scores dos riscos vinculados.")


class CompararCenariosResponse(BaseModel):
    """Os cenários ordenados por custo e risco. Nenhum vem marcado como escolhido (BR-028):
    `baseline` é só a referência da economia."""

    horizonte_anos: int
    quantidade_ativos: int
    baseline: NomeCenario
    cenarios: list[CenarioResultado]
    ordenado_por: list[str]
    observacao: str
