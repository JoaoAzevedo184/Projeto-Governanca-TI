from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

Nota = Annotated[Decimal, Field(ge=0, le=10, max_digits=4, decimal_places=2)]
Peso = Annotated[Decimal, Field(gt=0, le=100, max_digits=5, decimal_places=2)]


class CriterioScorecard(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    peso: Peso = Field(
        description="Percentual do critério. A soma dos pesos deve ser 100 (BR-029)."
    )


class AvaliacaoFornecedor(BaseModel):
    fornecedor_id: int
    notas: dict[str, Nota] = Field(
        description="Nota de 0 a 10 para cada critério, sem faltar nenhum."
    )


class ScorecardCreate(BaseModel):
    """Corpo de `POST /fornecedores/scorecard` (FR-011).

    Nota fora de 0–10, critério sem nota, critério desconhecido, critério ou fornecedor repetido
    são erros de validação (422). A soma dos pesos diferente de 100 é regra de negócio: o
    serviço recusa com 409 e `regra = BR-029`, registrada na auditoria (NFR-AUD-05).
    """

    periodo: str = Field(
        min_length=1, max_length=20, description="Rótulo do período, ex.: 2026-T3."
    )
    criterios: list[CriterioScorecard] = Field(min_length=1)
    avaliacoes: list[AvaliacaoFornecedor] = Field(min_length=1)

    @model_validator(mode="after")
    def _validar_consistencia(self) -> "ScorecardCreate":
        nomes = [c.nome for c in self.criterios]
        if len(set(nomes)) != len(nomes):
            raise ValueError("Há critério repetido.")
        fornecedores = [a.fornecedor_id for a in self.avaliacoes]
        if len(set(fornecedores)) != len(fornecedores):
            raise ValueError("Há fornecedor repetido.")
        for avaliacao in self.avaliacoes:
            faltam = set(nomes) - set(avaliacao.notas)
            sobram = set(avaliacao.notas) - set(nomes)
            if faltam:
                raise ValueError(
                    f"Fornecedor {avaliacao.fornecedor_id}: falta a nota de {sorted(faltam)}."
                )
            if sobram:
                raise ValueError(
                    f"Fornecedor {avaliacao.fornecedor_id}: nota de critério desconhecido "
                    f"{sorted(sobram)}."
                )
        return self


class PosicaoRanking(BaseModel):
    posicao: int
    fornecedor_id: int
    razao_social: str
    pontuacao: Decimal = Field(description="Soma ponderada, de 0 a 10, em 2 casas (half-up).")
    notas: dict[str, Decimal]


class ScorecardResponse(BaseModel):
    periodo: str
    criterios: list[CriterioScorecard]
    ranking: list[PosicaoRanking]
