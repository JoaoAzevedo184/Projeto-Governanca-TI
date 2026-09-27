from pydantic import BaseModel, Field


class ResponsavelCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=160)
    matricula: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=160)
    cargo: str | None = Field(default=None, max_length=120)
    localizacao: str | None = Field(default=None, max_length=120)
    setor_id: int | None = None
    ativo: bool = True


class ResponsavelResponse(ResponsavelCreate):
    id: int
    data_source: str

    model_config = {"from_attributes": True}
