from sqlalchemy.orm import Session

from app.core.audit import registrar_auditoria
from app.core.database import flush_ou_conflito
from app.models.responsavel import Responsavel
from app.models.usuario import Usuario
from app.schemas.responsavel import ResponsavelCreate


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
