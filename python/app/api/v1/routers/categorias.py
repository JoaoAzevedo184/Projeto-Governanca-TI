from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_perfil
from app.models.categoria import Categoria
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario
from app.schemas.categoria import CategoriaCreate, CategoriaResponse, CategoriaUpdate
from app.services import categoria_service

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get("", response_model=list[CategoriaResponse], dependencies=[Depends(get_current_user)])
def listar(db: Session = Depends(get_db)) -> list[Categoria]:
    return list(db.query(Categoria).order_by(Categoria.nome))


@router.post("", response_model=CategoriaResponse, status_code=201)
def criar(
    dados: CategoriaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN)),
) -> Categoria:
    return categoria_service.criar_categoria(db, dados, usuario)


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    dependencies=[Depends(get_current_user)],
)
def obter(categoria_id: int, db: Session = Depends(get_db)) -> Categoria:
    return categoria_service.obter_categoria(db, categoria_id)


@router.patch("/{categoria_id}", response_model=CategoriaResponse)
def atualizar(
    categoria_id: int,
    dados: CategoriaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN)),
) -> Categoria:
    return categoria_service.atualizar_categoria(db, categoria_id, dados, usuario)
