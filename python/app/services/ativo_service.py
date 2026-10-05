from typing import NoReturn

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import recusar_operacao, registrar_auditoria
from app.core.exceptions import RecursoNaoEncontradoError, RegraNegocioError
from app.models.ativo import Ativo
from app.models.categoria import Categoria
from app.models.enums import StatusAtivo, TipoAtivo
from app.models.fornecedor import Fornecedor
from app.models.usuario import Usuario
from app.schemas.ativo import AtivoCreate, AtivoUpdate

INDICE_CHAVE_UNICA = "ux_ativo_chave_licenca"
INDICE_NUMERO_SERIE_UNICO = "ativo_numero_serie_key"  # nome que o PostgreSQL deu ao UNIQUE
# Os dois únicos índices cujo conflito, sob concorrência, vira recusa de regra de negócio.
REGRA_POR_INDICE = {INDICE_CHAVE_UNICA: "BR-039", INDICE_NUMERO_SERIE_UNICO: "BR-001"}

COLUNAS_ORDENACAO = {
    "id": Ativo.id,
    "nome": Ativo.nome,
    "data_aquisicao": Ativo.data_aquisicao,
    "valor_compra": Ativo.valor_compra,
}


def _obter_categoria(db: Session, categoria_id: int) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise RecursoNaoEncontradoError(f"Categoria {categoria_id} não encontrada.")
    return categoria


def _obter_fornecedor(db: Session, fornecedor_id: int) -> Fornecedor:
    fornecedor = db.get(Fornecedor, fornecedor_id)
    if fornecedor is None:
        raise RecursoNaoEncontradoError(f"Fornecedor {fornecedor_id} não encontrado.")
    return fornecedor


def _id_do_ativo_com_chave(db: Session, chave: str) -> int | None:
    return db.scalar(select(Ativo.id).where(Ativo.chave_licenca == chave))


def _recusar_chave_duplicada(db: Session, usuario: Usuario, conflitante_id: int | None) -> NoReturn:
    """BR-039. Nem a mensagem nem a auditoria levam a chave (RI-08): só o ativo que a tem."""
    recusar_operacao(
        db,
        usuario_id=usuario.id,
        operacao="CRIAR",
        entidade="ativo",
        regra="BR-039",
        mensagem="Chave de licença já cadastrada em outro ativo (BR-039).",
        detalhe={"ativo_conflitante_id": conflitante_id},
    )


def _recusar_corrida(db: Session, usuario: Usuario, regra: str, dados: AtivoCreate) -> NoReturn:
    """O índice recusou o INSERT que a checagem prévia deixou passar (escritor concorrente)."""
    if regra == "BR-039":
        assert dados.chave_licenca is not None  # o índice é parcial: só vale com chave
        _recusar_chave_duplicada(db, usuario, _id_do_ativo_com_chave(db, dados.chave_licenca))
    conflitante_id = db.scalar(select(Ativo.id).where(Ativo.numero_serie == dados.numero_serie))
    recusar_operacao(
        db,
        usuario_id=usuario.id,
        operacao="CRIAR",
        entidade="ativo",
        regra=regra,
        mensagem="Número de série já cadastrado em outro ativo (BR-001).",
        detalhe={"ativo_conflitante_id": conflitante_id},
    )


def criar_ativo(db: Session, dados: AtivoCreate, usuario: Usuario) -> Ativo:
    categoria = _obter_categoria(db, dados.categoria_id)
    _obter_fornecedor(db, dados.fornecedor_id)

    if dados.numero_serie is not None:
        conflitante = db.scalar(select(Ativo).where(Ativo.numero_serie == dados.numero_serie))
        if conflitante is not None:
            registrar_auditoria(
                db,
                usuario_id=usuario.id,
                operacao="CRIAR",
                entidade="ativo",
                entidade_id=None,
                resultado="RECUSADO",
                regra_violada="BR-001",
            )
            db.commit()
            raise RegraNegocioError(
                f"Número de série já cadastrado no ativo {conflitante.id} ({conflitante.nome}).",
                regra="BR-001",
            )

    if dados.chave_licenca is not None:
        conflitante_id = _id_do_ativo_com_chave(db, dados.chave_licenca)
        if conflitante_id is not None:
            _recusar_chave_duplicada(db, usuario, conflitante_id)

    ativo = Ativo(
        nome=dados.nome,
        tipo=dados.tipo,
        categoria_id=dados.categoria_id,
        fornecedor_id=dados.fornecedor_id,
        numero_serie=dados.numero_serie,
        chave_licenca=dados.chave_licenca,
        data_aquisicao=dados.data_aquisicao,
        valor_compra=dados.valor_compra,
        vida_util_meses=dados.vida_util_meses or categoria.vida_util_meses,
        localizacao=dados.localizacao,
        observacoes=dados.observacoes,
        data_source="manual",
    )
    regra_da_corrida = None
    try:
        # Savepoint: no conflito só o INSERT é desfeito e a recusa ainda é auditada (NFR-AUD-05).
        with db.begin_nested():
            db.add(ativo)
            db.flush()
    except IntegrityError as erro:
        # A checagem acima não vê o escritor concorrente (ETL, carga D.8) que ainda não
        # confirmou; só o índice garante BR-001 e BR-039. Outro IntegrityError não é dessas regras.
        diagnostico = getattr(erro.orig, "diag", None)
        regra_da_corrida = REGRA_POR_INDICE.get(getattr(diagnostico, "constraint_name", ""))
        if regra_da_corrida is None:
            raise
    if regra_da_corrida is not None:  # fora do `except`: a mensagem do banco traz a chave (RI-08)
        _recusar_corrida(db, usuario, regra_da_corrida, dados)
    registrar_auditoria(
        db, usuario_id=usuario.id, operacao="CRIAR", entidade="ativo", entidade_id=ativo.id
    )
    db.commit()
    db.refresh(ativo)
    return ativo


def listar_ativos(
    db: Session,
    *,
    status: StatusAtivo | None = None,
    tipo: TipoAtivo | None = None,
    categoria_id: int | None = None,
    fornecedor_id: int | None = None,
    busca: str | None = None,
    pagina: int = 1,
    tamanho: int = 20,
    ordenar_por: str = "id",
    direcao: str = "asc",
) -> tuple[list[Ativo], int]:
    consulta = select(Ativo)
    if status is not None:
        consulta = consulta.where(Ativo.status == status)
    if tipo is not None:
        consulta = consulta.where(Ativo.tipo == tipo)
    if categoria_id is not None:
        consulta = consulta.where(Ativo.categoria_id == categoria_id)
    if fornecedor_id is not None:
        consulta = consulta.where(Ativo.fornecedor_id == fornecedor_id)
    if busca:
        termo = f"%{busca}%"
        consulta = consulta.where(or_(Ativo.nome.ilike(termo), Ativo.numero_serie.ilike(termo)))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0

    coluna = COLUNAS_ORDENACAO.get(ordenar_por, Ativo.id)
    coluna_ordenada = coluna.desc() if direcao == "desc" else coluna.asc()
    consulta = consulta.order_by(coluna_ordenada).offset((pagina - 1) * tamanho).limit(tamanho)

    itens = list(db.scalars(consulta))
    return itens, total


def obter_ativo(db: Session, ativo_id: int) -> Ativo:
    ativo = db.get(Ativo, ativo_id)
    if ativo is None:
        raise RecursoNaoEncontradoError(f"Ativo {ativo_id} não encontrado.")
    return ativo


def atualizar_ativo(db: Session, ativo_id: int, dados: AtivoUpdate, usuario: Usuario) -> Ativo:
    ativo = obter_ativo(db, ativo_id)
    alteracoes = dados.model_dump(exclude_unset=True)

    if "categoria_id" in alteracoes:
        _obter_categoria(db, alteracoes["categoria_id"])
    if "fornecedor_id" in alteracoes:
        _obter_fornecedor(db, alteracoes["fornecedor_id"])

    for campo, valor in alteracoes.items():
        setattr(ativo, campo, valor)

    db.flush()
    registrar_auditoria(
        db, usuario_id=usuario.id, operacao="ATUALIZAR", entidade="ativo", entidade_id=ativo.id
    )
    db.commit()
    db.refresh(ativo)
    return ativo
