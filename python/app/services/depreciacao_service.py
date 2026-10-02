from dataclasses import asdict
from datetime import date

from sqlalchemy.orm import Session

from app.models.ativo import Ativo
from app.schemas.depreciacao import DepreciacaoResponse
from app.services.ativo_service import obter_ativo
from app.utils.depreciacao import calcular


def calcular_para_ativo(ativo: Ativo, data_referencia: date | None = None) -> DepreciacaoResponse:
    """Depreciação do ativo na data de referência (padrão: hoje).

    ponytail: ativo BAIXADO deveria usar `baixa_ativo.data_baixa` (BR-015, AC-019), mas o
    registro de baixa só existe no Sprint 3; até lá nenhuma rota leva um ativo a BAIXADO,
    e o caso é coberto só no teste unitário da função pura.
    """
    referencia = data_referencia or date.today()
    resultado = calcular(
        ativo.valor_compra, ativo.data_aquisicao, ativo.vida_util_meses, referencia
    )
    return DepreciacaoResponse(ativo_id=ativo.id, data_referencia=referencia, **asdict(resultado))


def obter_depreciacao(db: Session, ativo_id: int) -> DepreciacaoResponse:
    return calcular_para_ativo(obter_ativo(db, ativo_id))
