from dataclasses import asdict
from datetime import date
from decimal import ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.models.ativo import Ativo
from app.models.enums import StatusAtivo
from app.schemas.depreciacao import DepreciacaoResponse
from app.services.ativo_service import obter_ativo
from app.utils.datas import hoje
from app.utils.depreciacao import CENTAVO, calcular


def calcular_para_ativo(ativo: Ativo, data_referencia: date | None = None) -> DepreciacaoResponse:
    """Depreciação do ativo na data de referência (padrão: hoje).

    Ativo baixado (BR-015, AC-019): a referência é `baixa.data_baixa`, nunca a data corrente, e o
    valor residual é o congelado em `baixa_ativo.valor_residual_baixa`; acumulada e percentual
    saem dele. `data_referencia` é ignorada nesse caso.
    """
    baixa = ativo.baixa if ativo.status == StatusAtivo.BAIXADO else None
    referencia = baixa.data_baixa if baixa is not None else data_referencia or hoje()
    resultado = calcular(
        ativo.valor_compra, ativo.data_aquisicao, ativo.vida_util_meses, referencia
    )
    resposta = DepreciacaoResponse(
        ativo_id=ativo.id, data_referencia=referencia, **asdict(resultado)
    )
    if baixa is not None:
        resposta.valor_residual = baixa.valor_residual_baixa
        resposta.depreciacao_acumulada = ativo.valor_compra - baixa.valor_residual_baixa
        resposta.percentual_depreciado = (
            resposta.depreciacao_acumulada / ativo.valor_compra * 100
        ).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    return resposta


def obter_depreciacao(db: Session, ativo_id: int) -> DepreciacaoResponse:
    return calcular_para_ativo(obter_ativo(db, ativo_id))
