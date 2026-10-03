from pydantic import BaseModel


class BancoSaude(BaseModel):
    status: str
    dialect: str


class SaudeResponse(BaseModel):
    """Estado da aplicação e do banco (FR-014, NFR-DIS-03, NFR-OBS-04, AC-053)."""

    status: str
    environment: str
    database: BancoSaude
    version: str
