from datetime import datetime

from pydantic import BaseModel


class ImportacaoResumo(BaseModel):
    lote_id: int
    nome_arquivo: str
    total_processado: int
    total_aceito: int
    total_rejeitado: int
    erros_url: str


class LoteImportacaoResponse(BaseModel):
    id: int
    nome_arquivo: str
    data_importacao: datetime
    usuario_id: int
    total_processado: int
    total_aceito: int
    total_rejeitado: int

    model_config = {"from_attributes": True}


class ErroImportacaoResponse(BaseModel):
    numero_linha: int
    campo: str
    valor_recebido: str | None
    motivo: str

    model_config = {"from_attributes": True}
