"""Recomendação rastreável (FR-013, BR-027, AC-051).

BR-027: nenhuma recomendação existe sem evidência. Não cabe numa constraint simples
(invariantes.md): o serviço recusa a lista vazia e cria a recomendação e as evidências na mesma
transação. O sistema só registra o que uma pessoa decidiu; não gera recomendação."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import recusar_operacao, registrar_auditoria
from app.core.exceptions import RecursoNaoEncontradoError
from app.models.ativo import Ativo
from app.models.enums import StatusRecomendacao, TipoEvidencia
from app.models.fornecedor import FornecedorAvaliacao
from app.models.licenca import Licenca
from app.models.recomendacao import Evidencia, Recomendacao
from app.models.responsavel import Responsavel
from app.models.risco import Risco
from app.models.usuario import Usuario
from app.schemas.recomendacao import EvidenciaCreate, RecomendacaoCreate
from app.utils.datas import hoje


def _validar_referencia(db: Session, evidencia: EvidenciaCreate) -> None:
    """A evidência aponta para o que existe, ou a recomendação não é gravada (404)."""
    ref = evidencia.referencia_id
    if evidencia.tipo == TipoEvidencia.RISCO:
        existe, nome = db.get(Risco, ref) is not None, "Risco"
    elif evidencia.tipo == TipoEvidencia.ATIVO:
        existe, nome = db.get(Ativo, ref) is not None, "Ativo"
    elif evidencia.tipo == TipoEvidencia.LICENCA:
        existe, nome = db.get(Licenca, ref) is not None, "Licença"
    elif evidencia.tipo == TipoEvidencia.SCORECARD:
        existe = (
            db.scalar(
                select(FornecedorAvaliacao.id)
                .where(FornecedorAvaliacao.fornecedor_id == ref)
                .limit(1)
            )
            is not None
        )
        nome = "Fornecedor com scorecard"
    else:  # INDICADOR, CENARIO, PREMISSA: sem registro, o schema já exigiu a descrição
        return
    if not existe:
        raise RecursoNaoEncontradoError(f"{nome} {ref} não encontrado.")


def criar_recomendacao(db: Session, dados: RecomendacaoCreate, usuario: Usuario) -> Recomendacao:
    if db.get(Responsavel, dados.responsavel_id) is None:
        raise RecursoNaoEncontradoError(f"Responsável {dados.responsavel_id} não encontrado.")

    if not dados.evidencias:
        recusar_operacao(
            db,
            usuario_id=usuario.id,
            operacao="CRIAR",
            entidade="recomendacao",
            regra="BR-027",
            mensagem="Nenhuma recomendação pode ser registrada sem ao menos uma evidência.",
            detalhe={"titulo": dados.titulo, "responsavel_id": dados.responsavel_id},
        )
    for evidencia in dados.evidencias:
        _validar_referencia(db, evidencia)

    # Uma só transação: a recomendação nunca existe sem as evidências (BR-027).
    recomendacao = Recomendacao(
        titulo=dados.titulo,
        contexto=dados.contexto,
        recomendacao=dados.recomendacao,
        alternativas=dados.alternativas,
        responsavel_id=dados.responsavel_id,
        data=dados.data or hoje(),
        status=dados.status.value,
        data_source="manual",
        evidencias=[
            Evidencia(tipo=e.tipo.value, referencia_id=e.referencia_id, descricao=e.descricao)
            for e in dados.evidencias
        ],
    )
    db.add(recomendacao)
    db.flush()
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        operacao="CRIAR",
        entidade="recomendacao",
        entidade_id=recomendacao.id,
        detalhe={
            "evidencias": [
                {"tipo": e.tipo, "referencia_id": e.referencia_id} for e in recomendacao.evidencias
            ]
        },
    )
    db.commit()
    db.refresh(recomendacao)
    return recomendacao


def obter_recomendacao(db: Session, recomendacao_id: int) -> Recomendacao:
    recomendacao = db.scalar(
        select(Recomendacao)
        .options(selectinload(Recomendacao.evidencias))
        .where(Recomendacao.id == recomendacao_id)
    )
    if recomendacao is None:
        raise RecursoNaoEncontradoError(f"Recomendação {recomendacao_id} não encontrada.")
    return recomendacao


def listar_recomendacoes(
    db: Session,
    *,
    status: StatusRecomendacao | None = None,
    pagina: int = 1,
    tamanho: int = 20,
) -> tuple[list[Recomendacao], int]:
    consulta = select(Recomendacao).options(selectinload(Recomendacao.evidencias))
    if status is not None:
        consulta = consulta.where(Recomendacao.status == status.value)
    total = db.scalar(select(func.count()).select_from(consulta.order_by(None).subquery())) or 0
    consulta = (
        consulta.order_by(Recomendacao.id.desc()).offset((pagina - 1) * tamanho).limit(tamanho)
    )
    return list(db.scalars(consulta)), total
