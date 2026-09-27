from pydantic import BaseModel, Field


class FornecedorCreate(BaseModel):
    razao_social: str = Field(min_length=2, max_length=160)
    cnpj: str | None = Field(default=None, max_length=18)
    contato: str | None = Field(default=None, max_length=120)
    telefone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=160)
    ativo: bool = True
    data_source: str = "sintetico"


class FornecedorResponse(FornecedorCreate):
    id: int

    model_config = {"from_attributes": True}
