from typing import NoReturn

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import registrar_auditoria
from app.core.database import flush_ou_conflito
from app.core.exceptions import RecursoNaoEncontradoError, RegraNegocioError
from app.models.ativo import Ativo
from app.models.enums import StatusAtivo
from app.models.historico import HistoricoTransferencia
from app.models.responsavel import Responsavel
from app.models.setor import Setor
from app.models.usuario import Usuario
from app.schemas.historico import VinculoCreate
from app.schemas.responsavel import ResponsavelCreate
from app.services.ativo_service import obter_ativo


def criar_responsavel(db: Session, dados: ResponsavelCreate, usuario: Usuario) -> Responsavel:
    responsavel = Responsavel(**dados.model_dump())
    db.add(responsavel)
    flush_ou_conflito(db, f"Responsável com matrícula '{responsavel.matricula}' já cadastrado.")
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        operacao="CRIAR",
        entidade="responsavel",
        entidade_id=responsavel.id,
    )
    db.commit()
    db.refresh(responsavel)
    return responsavel


def _recusar(db: Session, usuario: Usuario, ativo_id: int, regra: str, detalhe: str) -> NoReturn:
    """Registra a recusa na auditoria (NFR-AUD-05) antes de devolver o 409."""
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        operacao="CRIAR",
        entidade="historico_transferencia",
        entidade_id=None,
        resultado="RECUSADO",
        regra_violada=regra,
        detalhe={"ativo_id": ativo_id},
    )
    db.commit()
    raise RegraNegocioError(detalhe, regra=regra)


def atribuir_responsavel(
    db: Session, ativo_id: int, dados: VinculoCreate, usuario: Usuario
) -> HistoricoTransferencia:
    """Atribuição inicial ou transferência (FR-002): encerra o vínculo aberto, se houver,
    e cria o novo na mesma transação (BR-007, BR-008, AC-009, AC-010)."""
    # Lock no ativo serializa transferências concorrentes (BR-008/BR-009, invariantes.md).
    # FOR NO KEY UPDATE (key_share=True): não disputa o KEY SHARE que a FK de um insert externo
    # em historico_transferencia toma no ativo; assim o conflito com um escritor externo cai
    # no índice ux_vinculo_aberto (tratado abaixo) em vez de ser absorvido pelo lock.
    ativo = db.scalar(select(Ativo).where(Ativo.id == ativo_id).with_for_update(key_share=True))
    if ativo is None:
        raise RecursoNaoEncontradoError(f"Ativo {ativo_id} não encontrado.")
    responsavel = db.get(Responsavel, dados.responsavel_id)
    if responsavel is None:
        raise RecursoNaoEncontradoError(f"Responsável {dados.responsavel_id} não encontrado.")
    setor = db.get(Setor, dados.setor_id)
    if setor is None:
        raise RecursoNaoEncontradoError(f"Setor {dados.setor_id} não encontrado.")

    if ativo.status == StatusAtivo.BAIXADO:
        _recusar(db, usuario, ativo_id, "BR-009", "Ativo baixado não pode receber responsável.")
    if not responsavel.ativo or not setor.ativo:
        _recusar(db, usuario, ativo_id, "FR-002", "Responsável e setor devem estar ativos.")
    if dados.data_inicio < ativo.data_aquisicao:
        _recusar(
            db,
            usuario,
            ativo_id,
            "BR-010",
            f"data_inicio anterior à data de aquisição do ativo ({ativo.data_aquisicao}).",
        )

    aberto = db.scalar(
        select(HistoricoTransferencia).where(
            HistoricoTransferencia.ativo_id == ativo_id, HistoricoTransferencia.data_fim.is_(None)
        )
    )
    if aberto is not None and dados.data_inicio < aberto.data_inicio:
        _recusar(
            db,
            usuario,
            ativo_id,
            "BR-008",
            f"data_inicio anterior ao início do vínculo vigente ({aberto.data_inicio}).",
        )

    novo = HistoricoTransferencia(
        ativo_id=ativo_id,
        responsavel_id=dados.responsavel_id,
        setor_id=dados.setor_id,
        data_inicio=dados.data_inicio,
        motivo=dados.motivo,
        registrado_por_id=usuario.id,
        data_source="manual",
    )
    # Savepoint: no conflito desfaz só o encerramento e a inserção, e a recusa ainda é gravada
    # na auditoria antes do 409 (NFR-AUD-05).
    try:
        with db.begin_nested():
            if aberto is not None:
                aberto.data_fim = dados.data_inicio
                # Encerrar antes de inserir: o índice parcial ux_vinculo_aberto não é deferrable.
                db.flush()
                registrar_auditoria(
                    db,
                    usuario_id=usuario.id,
                    operacao="ATUALIZAR",
                    entidade="historico_transferencia",
                    entidade_id=aberto.id,
                    detalhe={"data_fim": dados.data_inicio.isoformat()},
                )
            db.add(novo)
            db.flush()
    except IntegrityError:
        # Sob concorrência, só o índice parcial garante BR-007 (ADR-006). Pela API o conflito é
        # inalcançável (o lock acima serializa as transferências); só um escritor externo que
        # insira direto na tabela (ETL, carga D.8) o provoca. Os demais IntegrityError possíveis
        # (FK, período) já foram barrados pelas validações acima.
        _recusar(
            db, usuario, ativo_id, "BR-007", "O ativo já possui um vínculo de responsável aberto."
        )
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        operacao="CRIAR",
        entidade="historico_transferencia",
        entidade_id=novo.id,
        detalhe={"ativo_id": ativo_id, "vinculo_encerrado_id": aberto.id if aberto else None},
    )
    db.commit()
    db.refresh(novo)
    return novo


def listar_historico(db: Session, ativo_id: int) -> list[HistoricoTransferencia]:
    """Todos os vínculos do ativo, do mais recente ao mais antigo (FR-002, AC-012)."""
    obter_ativo(db, ativo_id)
    consulta = (
        select(HistoricoTransferencia)
        .where(HistoricoTransferencia.ativo_id == ativo_id)
        .order_by(HistoricoTransferencia.data_inicio.desc(), HistoricoTransferencia.id.desc())
    )
    return list(db.scalars(consulta))
