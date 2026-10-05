"""Registro de riscos (FR-012, AC-050). O score é gerado pelo banco; a classificação vem da
função pura `utils/risco.classificar`. Toda escrita é auditada (BR-030)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import registrar_auditoria
from app.core.exceptions import RecursoNaoEncontradoError
from app.models.enums import CategoriaRisco, ClassificacaoRisco, RespostaRisco, StatusRisco
from app.models.responsavel import Responsavel
from app.models.risco import Risco
from app.models.usuario import Usuario
from app.schemas.risco import RiscoCreate, RiscoResponse, RiscoUpdate
from app.utils.risco import FAIXAS, classificar


def _resposta(risco: Risco) -> RiscoResponse:
    return RiscoResponse(
        id=risco.id,
        titulo=risco.titulo,
        descricao=risco.descricao,
        categoria=CategoriaRisco(risco.categoria),
        probabilidade=risco.probabilidade,
        impacto=risco.impacto,
        score=risco.score,
        classificacao=classificar(risco.score),
        resposta=RespostaRisco(risco.resposta),
        responsavel_id=risco.responsavel_id,
        status=StatusRisco(risco.status),
        gatilho=risco.gatilho,
        data_revisao=risco.data_revisao,
        data_source=risco.data_source,
        criado_em=risco.criado_em,
        atualizado_em=risco.atualizado_em,
    )


def _validar_responsavel(db: Session, responsavel_id: int | None) -> None:
    if responsavel_id is not None and db.get(Responsavel, responsavel_id) is None:
        raise RecursoNaoEncontradoError(f"Responsável {responsavel_id} não encontrado.")


def _obter(db: Session, risco_id: int) -> Risco:
    risco = db.get(Risco, risco_id)
    if risco is None:
        raise RecursoNaoEncontradoError(f"Risco {risco_id} não encontrado.")
    return risco


def criar_risco(db: Session, dados: RiscoCreate, usuario: Usuario) -> RiscoResponse:
    _validar_responsavel(db, dados.responsavel_id)
    risco = Risco(**dados.model_dump(), data_source="manual")
    db.add(risco)
    db.flush()
    registrar_auditoria(
        db, usuario_id=usuario.id, operacao="CRIAR", entidade="risco", entidade_id=risco.id
    )
    db.commit()
    db.refresh(risco)  # traz o score gerado pelo banco
    return _resposta(risco)


def listar_riscos(
    db: Session,
    *,
    categoria: CategoriaRisco | None = None,
    status: StatusRisco | None = None,
    classificacao: ClassificacaoRisco | None = None,
    pagina: int = 1,
    tamanho: int = 20,
) -> tuple[list[RiscoResponse], int]:
    consulta = select(Risco)
    if categoria is not None:
        consulta = consulta.where(Risco.categoria == categoria.value)
    if status is not None:
        consulta = consulta.where(Risco.status == status.value)
    if classificacao is not None:
        minimo, maximo = FAIXAS[classificacao]
        consulta = consulta.where(Risco.score.between(minimo, maximo))
    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    consulta = consulta.order_by(Risco.score.desc(), Risco.id).offset((pagina - 1) * tamanho)
    return [_resposta(r) for r in db.scalars(consulta.limit(tamanho))], total


def obter_risco(db: Session, risco_id: int) -> RiscoResponse:
    return _resposta(_obter(db, risco_id))


def atualizar_risco(
    db: Session, risco_id: int, dados: RiscoUpdate, usuario: Usuario
) -> RiscoResponse:
    risco = _obter(db, risco_id)
    alteracoes = dados.model_dump(exclude_unset=True)
    for campo in ("titulo", "categoria", "probabilidade", "impacto", "resposta", "status"):
        if campo in alteracoes and alteracoes[campo] is None:
            alteracoes.pop(campo)  # esses campos não são anuláveis: null é ignorado
    if "responsavel_id" in alteracoes:
        _validar_responsavel(db, alteracoes["responsavel_id"])
    for campo, valor in alteracoes.items():
        setattr(risco, campo, valor)
    db.flush()
    registrar_auditoria(
        db, usuario_id=usuario.id, operacao="ATUALIZAR", entidade="risco", entidade_id=risco.id
    )
    db.commit()
    db.refresh(risco)
    return _resposta(risco)
