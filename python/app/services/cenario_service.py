"""Comparação de cenários e TCO de 5 anos (FR-010, BR-028, AC-052).

Os cenários só são calculados: não há tabela de cenário (modelo-fisico.md), e a resposta não é
persistida nem auditada, como uma consulta. O sistema ordena por custo e risco e não escolhe; a
decisão é humana e se registra em `/recomendacoes` (FR-013)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import RecursoNaoEncontradoError
from app.models.ativo import Ativo
from app.models.enums import NomeCenario, StatusAtivo
from app.models.risco import Risco
from app.schemas.cenario import (
    CenarioResultado,
    CompararCenariosCreate,
    CompararCenariosResponse,
)
from app.utils.cenario import HORIZONTE_ANOS, EntradaCenario, comparar, escolher_baseline

OBSERVACAO = "A seleção da alternativa é decisão humana e deve ser registrada em /recomendacoes."


def comparar_cenarios(db: Session, dados: CompararCenariosCreate) -> CompararCenariosResponse:
    ids = {r for c in dados.cenarios for r in c.riscos_ids}
    scores = {
        risco_id: score
        for risco_id, score in db.execute(select(Risco.id, Risco.score).where(Risco.id.in_(ids)))
    }
    for risco_id in sorted(ids):
        if risco_id not in scores:
            raise RecursoNaoEncontradoError(f"Risco {risco_id} não encontrado.")

    quantidade = dados.quantidade_ativos
    if quantidade is None:
        quantidade = (
            db.scalar(
                select(func.count()).select_from(Ativo).where(Ativo.status != StatusAtivo.BAIXADO)
            )
            or 0
        )

    entradas = [
        EntradaCenario(
            nome=c.nome.value,
            capex=c.capex,
            opex_anual=c.opex_anual,
            score_risco=sum(scores[r] for r in c.riscos_ids),
        )
        for c in dados.cenarios
    ]
    baseline = escolher_baseline([e.nome for e in entradas])
    resultados = comparar(entradas, quantidade, baseline)
    return CompararCenariosResponse(
        horizonte_anos=HORIZONTE_ANOS,
        quantidade_ativos=quantidade,
        baseline=NomeCenario(baseline),
        cenarios=[
            CenarioResultado(
                nome=NomeCenario(r.nome),
                capex=r.capex,
                opex_anual=r.opex_anual,
                tco_5_anos=r.tco_5_anos,
                custo_por_ativo_ano=r.custo_por_ativo_ano,
                economia_vs_baseline=r.economia_vs_baseline,
                score_risco=r.score_risco,
            )
            for r in resultados
        ],
        ordenado_por=["tco_5_anos", "score_risco"],
        observacao=OBSERVACAO,
    )
