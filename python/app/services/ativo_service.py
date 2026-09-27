from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.audit import registrar_auditoria
from app.core.exceptions import RecursoNaoEncontradoError, RegraNegocioError
from app.models.ativo import Ativo
from app.models.categoria import Categoria
from app.models.enums import StatusAtivo, TipoAtivo
from app.models.fornecedor import Fornecedor
from app.models.usuario import Usuario
from app.schemas.ativo import AtivoCreate, AtivoUpdate

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
        data_source="importacao",
    )
    db.add(ativo)
    db.flush()
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
