from sqlalchemy.orm import Session

from app.core.audit import registrar_auditoria
from app.core.database import flush_ou_conflito
from app.models.setor import Setor
from app.models.usuario import Usuario
from app.schemas.setor import SetorCreate


def criar_setor(db: Session, dados: SetorCreate, usuario: Usuario) -> Setor:
    setor = Setor(**dados.model_dump())
    db.add(setor)
    flush_ou_conflito(db, f"Setor '{setor.nome}' já cadastrado.")
    registrar_auditoria(
        db, usuario_id=usuario.id, operacao="CRIAR", entidade="setor", entidade_id=setor.id
    )
    db.commit()
    db.refresh(setor)
    return setor
