from pydantic import BaseModel, Field

from app.models.enums import TipoAtivo


class CategoriaCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    descricao: str | None = Field(default=None, max_length=255)
    vida_util_meses: int = Field(gt=0)
    tipo_aplicavel: TipoAtivo
    ativa: bool = True


class CategoriaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=80)
    descricao: str | None = Field(default=None, max_length=255)
    vida_util_meses: int | None = Field(default=None, gt=0)
    tipo_aplicavel: TipoAtivo | None = None
    ativa: bool | None = None


class CategoriaResponse(CategoriaCreate):
    id: int

    model_config = {"from_attributes": True}
