from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import recusar_operacao, registrar_auditoria
from app.core.exceptions import RecursoNaoEncontradoError
from app.models.ativo import Ativo
from app.models.baixa import BaixaAtivo
from app.models.enums import MotivoBaixa, StatusAtivo
from app.models.historico import HistoricoTransferencia
from app.models.usuario import Usuario
from app.schemas.baixa import BaixaCreate
from app.utils.datas import hoje
from app.utils.depreciacao import calcular

JUSTIFICATIVA_MINIMA = 10


def registrar_baixa(db: Session, ativo_id: int, dados: BaixaCreate, usuario: Usuario) -> BaixaAtivo:
    """Baixa do ativo em transação única (FR-005, AC-027): status BAIXADO, vínculo de
    responsável aberto encerrado (BR-012) e valor residual congelado (BR-015)."""

    def recusar(regra: str, mensagem: str) -> None:
        recusar_operacao(
            db,
            usuario_id=usuario.id,
            operacao="CRIAR",
            entidade="baixa_ativo",
            regra=regra,
            mensagem=mensagem,
            detalhe={"ativo_id": ativo_id},
        )

    # Lock no ativo serializa baixas concorrentes: a segunda enxerga BAIXADO e recebe BR-024.
    # FOR NO KEY UPDATE pelo mesmo motivo do lock de atribuir_responsavel (FK de insert externo).
    ativo = db.scalar(select(Ativo).where(Ativo.id == ativo_id).with_for_update(key_share=True))
    if ativo is None:
        raise RecursoNaoEncontradoError(f"Ativo {ativo_id} não encontrado.")

    if ativo.status == StatusAtivo.BAIXADO:
        recusar("BR-024", "Ativo já baixado não pode ser baixado novamente.")
    justificativa = (dados.justificativa or "").strip()
    if dados.motivo == MotivoBaixa.OUTRO and len(justificativa) < JUSTIFICATIVA_MINIMA:
        recusar("BR-023", "Motivo OUTRO exige justificativa de ao menos 10 caracteres.")
    if dados.data_baixa > hoje():
        recusar("BR-022", "A data da baixa não pode ser futura.")
    if dados.data_baixa < ativo.data_aquisicao:
        recusar(
            "BR-022", f"A data da baixa é anterior à data de aquisição ({ativo.data_aquisicao})."
        )
    if dados.destinacao is None:
        recusar("BR-026", "Toda baixa exige destinação registrada.")

    aberto = db.scalar(
        select(HistoricoTransferencia).where(
            HistoricoTransferencia.ativo_id == ativo_id, HistoricoTransferencia.data_fim.is_(None)
        )
    )
    if aberto is not None and dados.data_baixa < aberto.data_inicio:
        recusar(
            "BR-012",
            "A data da baixa é anterior ao início do vínculo de responsável aberto "
            f"({aberto.data_inicio}); o vínculo não pode ser encerrado antes de começar.",
        )

    residual = calcular(
        ativo.valor_compra, ativo.data_aquisicao, ativo.vida_util_meses, dados.data_baixa
    ).valor_residual
    baixa = BaixaAtivo(
        ativo_id=ativo_id,
        motivo=dados.motivo,
        justificativa=justificativa or None,
        data_baixa=dados.data_baixa,
        destinacao=dados.destinacao,
        valor_residual_baixa=residual,
        registrado_por_id=usuario.id,
        data_source="manual",
    )
    # Savepoint: se o UNIQUE (ativo_id) recusar, só o que foi feito aqui é desfeito e a recusa
    # ainda é gravada na auditoria antes do 409 (NFR-AUD-05).
    try:
        with db.begin_nested():
            if aberto is not None:
                aberto.data_fim = dados.data_baixa
                # Encerrar o vínculo e gravar a baixa são a mesma transação (BR-012).
                db.flush()
                registrar_auditoria(
                    db,
                    usuario_id=usuario.id,
                    operacao="ATUALIZAR",
                    entidade="historico_transferencia",
                    entidade_id=aberto.id,
                    detalhe={"data_fim": dados.data_baixa.isoformat(), "origem": "baixa"},
                )
            db.add(baixa)
            ativo.status = StatusAtivo.BAIXADO
            db.flush()
    except IntegrityError:
        # Pela API o conflito é inalcançável (o lock acima serializa as baixas); só um escritor
        # externo que insira direto em baixa_ativo o provoca. O UNIQUE é a garantia (BR-024).
        db.expire_all()
        recusar("BR-024", "Ativo já baixado não pode ser baixado novamente.")
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        operacao="CRIAR",
        entidade="baixa_ativo",
        entidade_id=baixa.id,
        detalhe={"ativo_id": ativo_id, "vinculo_encerrado_id": aberto.id if aberto else None},
    )
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        operacao="ATUALIZAR",
        entidade="ativo",
        entidade_id=ativo_id,
        detalhe={"status": StatusAtivo.BAIXADO.value},
    )
    db.commit()
    db.refresh(baixa)
    return baixa
