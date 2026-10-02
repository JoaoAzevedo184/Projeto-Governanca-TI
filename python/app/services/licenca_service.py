from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import recusar_operacao, registrar_auditoria
from app.core.exceptions import RecursoNaoEncontradoError
from app.models.ativo import Ativo
from app.models.enums import TipoAtivo, TipoLicenciamento
from app.models.fornecedor import Fornecedor
from app.models.licenca import Licenca, LicencaVinculo
from app.models.usuario import Usuario
from app.schemas.licenca import (
    LicencaCreate,
    LicencaResponse,
    LicencaUpdate,
    VinculoLicencaCreate,
)
from app.utils.datas import hoje
from app.utils.mascaramento import chave_para_perfil


def _contar_em_uso(db: Session, ids: list[int]) -> dict[int, int]:
    """Quantidade em uso por licença: COUNT dos vínculos ativos (BR-021, ADR-008)."""
    consulta = (
        select(LicencaVinculo.licenca_id, func.count())
        .where(LicencaVinculo.licenca_id.in_(ids), LicencaVinculo.ativo_vinculo.is_(True))
        .group_by(LicencaVinculo.licenca_id)
    )
    return dict(db.execute(consulta).tuples().all())


def _resposta(licenca: Licenca, em_uso: int, usuario: Usuario, *, detalhe: bool) -> LicencaResponse:
    return LicencaResponse(
        id=licenca.id,
        tipo_licenciamento=TipoLicenciamento(licenca.tipo_licenciamento),
        ativo_id=licenca.ativo_id,
        software=licenca.software,
        fornecedor_id=licenca.fornecedor_id,
        chave_licenca=chave_para_perfil(licenca.chave_licenca, usuario.perfil, detalhe=detalhe)
        or "",
        quantidade_contratada=licenca.quantidade_contratada,
        quantidade_em_uso=em_uso,
        saldo=licenca.quantidade_contratada - em_uso,
        data_inicio_vigencia=licenca.data_inicio_vigencia,
        data_expiracao=licenca.data_expiracao,
        dias_para_expiracao=(licenca.data_expiracao - hoje()).days,
        valor_total=licenca.valor_total,
        data_source=licenca.data_source,
    )


def _obter(db: Session, licenca_id: int, *, travar: bool = False) -> Licenca:
    consulta = select(Licenca).where(Licenca.id == licenca_id)
    if travar:
        # Lock na licença serializa vinculações e edições concorrentes: a contagem de BR-018
        # só vale se ninguém vincula entre o COUNT e o INSERT. FOR NO KEY UPDATE (key_share=True)
        # não disputa o KEY SHARE que a FK de um insert externo em licenca_vinculo toma.
        consulta = consulta.with_for_update(key_share=True)
    licenca = db.scalar(consulta)
    if licenca is None:
        raise RecursoNaoEncontradoError(f"Licença {licenca_id} não encontrada.")
    return licenca


def criar_licenca(db: Session, dados: LicencaCreate, usuario: Usuario) -> LicencaResponse:
    def recusar(regra: str, mensagem: str) -> None:
        recusar_operacao(
            db,
            usuario_id=usuario.id,
            operacao="CRIAR",
            entidade="licenca",
            regra=regra,
            mensagem=mensagem,
            detalhe={"tipo_licenciamento": dados.tipo_licenciamento.value},
        )

    if db.get(Fornecedor, dados.fornecedor_id) is None:
        raise RecursoNaoEncontradoError(f"Fornecedor {dados.fornecedor_id} não encontrado.")
    if dados.ativo_id is not None:
        ativo = db.get(Ativo, dados.ativo_id)
        if ativo is None:
            raise RecursoNaoEncontradoError(f"Ativo {dados.ativo_id} não encontrado.")
        if ativo.tipo != TipoAtivo.SOFTWARE:
            # O CHECK não enxerga outra tabela (modelo-fisico.md): o serviço valida.
            recusar("FR-004", "Licença PERPETUA deve apontar para um ativo do tipo SOFTWARE.")
    if dados.data_expiracao <= dados.data_inicio_vigencia:
        recusar("BR-019", "A data de expiração deve ser posterior ao início da vigência.")

    licenca = Licenca(**dados.model_dump(), data_source="manual")
    db.add(licenca)
    db.flush()
    registrar_auditoria(
        db, usuario_id=usuario.id, operacao="CRIAR", entidade="licenca", entidade_id=licenca.id
    )
    db.commit()
    db.refresh(licenca)
    return _resposta(licenca, 0, usuario, detalhe=True)


def listar_licencas(
    db: Session,
    usuario: Usuario,
    *,
    tipo_licenciamento: TipoLicenciamento | None = None,
    fornecedor_id: int | None = None,
    pagina: int = 1,
    tamanho: int = 20,
) -> tuple[list[LicencaResponse], int]:
    consulta = select(Licenca)
    if tipo_licenciamento is not None:
        consulta = consulta.where(Licenca.tipo_licenciamento == tipo_licenciamento.value)
    if fornecedor_id is not None:
        consulta = consulta.where(Licenca.fornecedor_id == fornecedor_id)
    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    consulta = consulta.order_by(Licenca.id).offset((pagina - 1) * tamanho).limit(tamanho)
    licencas = list(db.scalars(consulta))
    em_uso = _contar_em_uso(db, [licenca.id for licenca in licencas])
    # Listagem: a chave sai sempre mascarada (RI-08).
    itens = [_resposta(lic, em_uso.get(lic.id, 0), usuario, detalhe=False) for lic in licencas]
    return itens, total


def obter_licenca(db: Session, licenca_id: int, usuario: Usuario) -> LicencaResponse:
    licenca = _obter(db, licenca_id)
    em_uso = _contar_em_uso(db, [licenca_id]).get(licenca_id, 0)
    return _resposta(licenca, em_uso, usuario, detalhe=True)


def atualizar_licenca(
    db: Session, licenca_id: int, dados: LicencaUpdate, usuario: Usuario
) -> LicencaResponse:
    licenca = _obter(db, licenca_id, travar=True)
    alteracoes = dados.model_dump(exclude_unset=True)

    def recusar(regra: str, mensagem: str) -> None:
        recusar_operacao(
            db,
            usuario_id=usuario.id,
            operacao="ATUALIZAR",
            entidade="licenca",
            regra=regra,
            mensagem=mensagem,
            detalhe={"licenca_id": licenca_id},
        )

    if "fornecedor_id" in alteracoes and db.get(Fornecedor, alteracoes["fornecedor_id"]) is None:
        raise RecursoNaoEncontradoError(f"Fornecedor {alteracoes['fornecedor_id']} não encontrado.")
    inicio = alteracoes.get("data_inicio_vigencia", licenca.data_inicio_vigencia)
    expiracao = alteracoes.get("data_expiracao", licenca.data_expiracao)
    if expiracao <= inicio:
        recusar("BR-019", "A data de expiração deve ser posterior ao início da vigência.")
    em_uso = _contar_em_uso(db, [licenca_id]).get(licenca_id, 0)
    if alteracoes.get("quantidade_contratada", licenca.quantidade_contratada) < em_uso:
        recusar(
            "BR-018",
            f"A quantidade contratada não pode ficar abaixo da quantidade em uso ({em_uso}).",
        )

    for campo, valor in alteracoes.items():
        setattr(licenca, campo, valor)
    db.flush()
    registrar_auditoria(
        db, usuario_id=usuario.id, operacao="ATUALIZAR", entidade="licenca", entidade_id=licenca.id
    )
    db.commit()
    db.refresh(licenca)
    return _resposta(licenca, em_uso, usuario, detalhe=True)


def listar_vinculos(db: Session, licenca_id: int) -> list[LicencaVinculo]:
    """Todos os vínculos da licença, ativos e desvinculados, do mais recente ao mais antigo."""
    _obter(db, licenca_id)
    consulta = (
        select(LicencaVinculo)
        .where(LicencaVinculo.licenca_id == licenca_id)
        .order_by(LicencaVinculo.id.desc())
    )
    return list(db.scalars(consulta))


def vincular(
    db: Session, licenca_id: int, dados: VinculoLicencaCreate, usuario: Usuario
) -> LicencaVinculo:
    """Instala a licença numa máquina (FR-004, AC-021, AC-025). Recusa excedente (BR-018) e
    licença vencida (BR-020), registrando a tentativa na auditoria (NFR-AUD-05)."""

    def recusar(regra: str, mensagem: str) -> None:
        recusar_operacao(
            db,
            usuario_id=usuario.id,
            operacao="CRIAR",
            entidade="licenca_vinculo",
            regra=regra,
            mensagem=mensagem,
            detalhe={"licenca_id": licenca_id, "ativo_id": dados.ativo_id},
        )

    licenca = _obter(db, licenca_id, travar=True)
    maquina = db.get(Ativo, dados.ativo_id)
    if maquina is None:
        raise RecursoNaoEncontradoError(f"Ativo {dados.ativo_id} não encontrado.")

    if licenca.data_expiracao < hoje():
        recusar("BR-020", f"Licença vencida em {licenca.data_expiracao}: sem novas vinculações.")
    if maquina.tipo != TipoAtivo.HARDWARE:
        recusar("FR-004", "O vínculo aponta para a máquina hospedeira, um ativo HARDWARE.")
    ja_vinculada = db.scalar(
        select(LicencaVinculo.id).where(
            LicencaVinculo.licenca_id == licenca_id,
            LicencaVinculo.ativo_id == dados.ativo_id,
            LicencaVinculo.ativo_vinculo.is_(True),
        )
    )
    if ja_vinculada is not None:
        recusar("FR-004", "A licença já está vinculada a esta máquina.")
    em_uso = _contar_em_uso(db, [licenca_id]).get(licenca_id, 0)
    if em_uso >= licenca.quantidade_contratada:
        recusar(
            "BR-018",
            "A quantidade em uso não pode exceder a quantidade contratada "
            f"({licenca.quantidade_contratada}).",
        )

    vinculo = LicencaVinculo(
        licenca_id=licenca_id,
        ativo_id=dados.ativo_id,
        data_vinculo=dados.data_vinculo or hoje(),
        ativo_vinculo=True,
        data_source="manual",
    )
    try:
        with db.begin_nested():
            db.add(vinculo)
            db.flush()
    except IntegrityError:
        # Pela API o conflito é inalcançável (o lock na licença serializa as vinculações); só um
        # escritor externo que insira direto em licenca_vinculo (ETL, carga D.8) o provoca. O
        # índice parcial ux_licenca_ativo é a garantia.
        db.expire_all()
        recusar("FR-004", "A licença já está vinculada a esta máquina.")
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        operacao="CRIAR",
        entidade="licenca_vinculo",
        entidade_id=vinculo.id,
        detalhe={"licenca_id": licenca_id, "ativo_id": dados.ativo_id},
    )
    db.commit()
    db.refresh(vinculo)
    return vinculo


def desvincular(db: Session, licenca_id: int, ativo_id: int, usuario: Usuario) -> None:
    """Desvínculo lógico (`ativo_vinculo = false`): a quantidade em uso cai sozinha, porque é
    derivada do COUNT (AC-026). Nenhum registro é apagado (RI-06)."""
    _obter(db, licenca_id, travar=True)
    vinculo = db.scalar(
        select(LicencaVinculo).where(
            LicencaVinculo.licenca_id == licenca_id,
            LicencaVinculo.ativo_id == ativo_id,
            LicencaVinculo.ativo_vinculo.is_(True),
        )
    )
    if vinculo is None:
        raise RecursoNaoEncontradoError(
            f"A licença {licenca_id} não tem vínculo ativo com o ativo {ativo_id}."
        )
    vinculo.ativo_vinculo = False
    db.flush()
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        operacao="EXCLUIR",
        entidade="licenca_vinculo",
        entidade_id=vinculo.id,
        detalhe={"licenca_id": licenca_id, "ativo_id": ativo_id, "desvinculo": "logico"},
    )
    db.commit()
