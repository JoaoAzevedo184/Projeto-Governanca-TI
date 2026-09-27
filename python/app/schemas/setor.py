from pydantic import BaseModel, Field


class SetorCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    sigla: str | None = Field(default=None, max_length=12)
    ativo: bool = True


class SetorResponse(SetorCreate):
    id: int

    model_config = {"from_attributes": True}
