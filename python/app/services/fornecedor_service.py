from sqlalchemy.orm import Session

from app.core.audit import registrar_auditoria
from app.core.database import flush_ou_conflito
from app.models.fornecedor import Fornecedor
from app.models.usuario import Usuario
from app.schemas.fornecedor import FornecedorCreate


def criar_fornecedor(db: Session, dados: FornecedorCreate, usuario: Usuario) -> Fornecedor:
    fornecedor = Fornecedor(**dados.model_dump())
    db.add(fornecedor)
    flush_ou_conflito(db, f"Fornecedor com CNPJ '{fornecedor.cnpj}' já cadastrado.")
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        operacao="CRIAR",
        entidade="fornecedor",
        entidade_id=fornecedor.id,
    )
    db.commit()
    db.refresh(fornecedor)
    return fornecedor
