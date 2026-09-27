from sqlalchemy.orm import Session

from app.core.audit import registrar_auditoria
from app.core.database import flush_ou_conflito
from app.core.exceptions import RecursoNaoEncontradoError
from app.models.categoria import Categoria
from app.models.usuario import Usuario
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate


def obter_categoria(db: Session, categoria_id: int) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise RecursoNaoEncontradoError(f"Categoria {categoria_id} não encontrada.")
    return categoria


def criar_categoria(db: Session, dados: CategoriaCreate, usuario: Usuario) -> Categoria:
    categoria = Categoria(**dados.model_dump())
    db.add(categoria)
    flush_ou_conflito(db, f"Categoria '{categoria.nome}' já cadastrada.")
    registrar_auditoria(
        db, usuario_id=usuario.id, operacao="CRIAR", entidade="categoria", entidade_id=categoria.id
    )
    db.commit()
    db.refresh(categoria)
    return categoria


def atualizar_categoria(
    db: Session, categoria_id: int, dados: CategoriaUpdate, usuario: Usuario
) -> Categoria:
    categoria = obter_categoria(db, categoria_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(categoria, campo, valor)
    flush_ou_conflito(db, f"Categoria '{categoria.nome}' já cadastrada.")
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        operacao="ATUALIZAR",
        entidade="categoria",
        entidade_id=categoria.id,
    )
    db.commit()
    db.refresh(categoria)
    return categoria
