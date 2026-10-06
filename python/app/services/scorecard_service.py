"""Scorecard de fornecedores (FR-011, BR-029, AC-048, AC-049).

Persiste uma linha de `fornecedor_avaliacao` por fornecedor e critério e devolve a pontuação
ponderada e o ranking, que são derivados na hora (nada de pontuação armazenada)."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import recusar_operacao, registrar_auditoria
from app.core.exceptions import RecursoNaoEncontradoError
from app.models.fornecedor import Fornecedor, FornecedorAvaliacao
from app.models.usuario import Usuario
from app.schemas.scorecard import (
    CriterioScorecard,
    PosicaoRanking,
    ScorecardCreate,
    ScorecardResponse,
)
from app.utils.scorecard import CENTAVO, pesos_somam_100, pontuacao, ranking, soma_dos_pesos


def registrar_scorecard(
    db: Session, dados: ScorecardCreate, usuario: Usuario, *, origem: str = "manual"
) -> ScorecardResponse:
    ids = [a.fornecedor_id for a in dados.avaliacoes]
    fornecedores = {f.id: f for f in db.scalars(select(Fornecedor).where(Fornecedor.id.in_(ids)))}
    for fornecedor_id in ids:
        if fornecedor_id not in fornecedores:
            raise RecursoNaoEncontradoError(f"Fornecedor {fornecedor_id} não encontrado.")

    pesos = {c.nome: c.peso for c in dados.criterios}
    if not pesos_somam_100(list(pesos.values())):
        recusar_operacao(
            db,
            usuario_id=usuario.id,
            operacao="CRIAR",
            entidade="fornecedor_avaliacao",
            regra="BR-029",
            mensagem=(
                f"Os pesos dos critérios somam {soma_dos_pesos(list(pesos.values()))}%, "
                "e devem somar exatamente 100%."
            ),
            detalhe={
                "periodo": dados.periodo,
                "soma_dos_pesos": str(soma_dos_pesos(list(pesos.values()))),
            },
        )

    pontuacoes: dict[int, Decimal] = {}
    for avaliacao in dados.avaliacoes:
        linhas = [
            FornecedorAvaliacao(
                fornecedor_id=avaliacao.fornecedor_id,
                criterio=criterio,
                peso=peso,
                nota=avaliacao.notas[criterio],
                periodo=dados.periodo,
                data_source=origem,
            )
            for criterio, peso in pesos.items()
        ]
        db.add_all(linhas)
        db.flush()
        pontuacoes[avaliacao.fornecedor_id] = pontuacao(avaliacao.notas, pesos)
        registrar_auditoria(
            db,
            usuario_id=usuario.id,
            operacao="CRIAR",
            entidade="fornecedor_avaliacao",
            entidade_id=linhas[0].id,
            detalhe={
                "fornecedor_id": avaliacao.fornecedor_id,
                "periodo": dados.periodo,
                "linhas": [linha.id for linha in linhas],
                "pontuacao": str(pontuacoes[avaliacao.fornecedor_id]),
            },
        )
    db.commit()

    notas = {
        a.fornecedor_id: {k: v.quantize(CENTAVO) for k, v in a.notas.items()}
        for a in dados.avaliacoes
    }
    return ScorecardResponse(
        periodo=dados.periodo,
        criterios=[
            CriterioScorecard(nome=c.nome, peso=c.peso.quantize(CENTAVO)) for c in dados.criterios
        ],
        ranking=[
            PosicaoRanking(
                posicao=posicao,
                fornecedor_id=ident,
                razao_social=fornecedores[ident].razao_social,
                pontuacao=nota,
                notas=notas[ident],
            )
            for posicao, ident, nota in ranking(pontuacoes)
        ],
    )
