import logging
from collections.abc import Sequence

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("itam")


class ErroDominio(Exception):
    """Erro de domínio da API, convertido no padrão de erros (docs/spec/padrao-de-erros.md)."""

    status_code: int = 400
    titulo: str = "Erro"
    tipo: str = "/erros/erro"

    def __init__(self, detalhe: str, regra: str | None = None):
        self.detalhe = detalhe
        self.regra = regra
        super().__init__(detalhe)


class RegraNegocioError(ErroDominio):
    status_code = 409
    titulo = "Operação recusada por regra de negócio"
    tipo = "/erros/regra-de-negocio"


class RecursoNaoEncontradoError(ErroDominio):
    status_code = 404
    titulo = "Recurso não encontrado"
    tipo = "/erros/nao-encontrado"


class NaoAutenticadoError(ErroDominio):
    status_code = 401
    titulo = "Não autenticado"
    tipo = "/erros/nao-autenticado"


class PermissaoNegadaError(ErroDominio):
    status_code = 403
    titulo = "Perfil sem permissão"
    tipo = "/erros/permissao-negada"

    def __init__(self, perfil: str):
        super().__init__(f"Perfil '{perfil}' não tem permissão para esta operação.", regra="FR-015")


class ErroValidacaoArquivo(ErroDominio):
    status_code = 422
    titulo = "Arquivo inválido"
    tipo = "/erros/arquivo-invalido"


def _payload(
    status: int,
    titulo: str,
    tipo: str,
    detalhe: str,
    instancia: str,
    regra: str | None = None,
    erros: Sequence[object] | None = None,
) -> dict:
    return {
        "tipo": tipo,
        "titulo": titulo,
        "status": status,
        "detalhe": detalhe,
        "instancia": instancia,
        "regra": regra,
        "erros": list(erros) if erros else [],
    }


_TITULOS_HTTP = {
    400: "Requisição inválida",
    401: "Não autenticado",
    403: "Perfil sem permissão",
    404: "Recurso não encontrado",
    405: "Método não permitido",
}


def registrar_handlers_erro(app: FastAPI) -> None:
    @app.exception_handler(ErroDominio)
    async def _erro_dominio(request: Request, exc: ErroDominio) -> JSONResponse:
        if exc.regra:
            logger.info(
                "Operação recusada por regra de negócio",
                extra={
                    "regra": exc.regra,
                    "status": exc.status_code,
                    "usuario_id": getattr(request.state, "usuario_id", None),
                },
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(
                exc.status_code, exc.titulo, exc.tipo, exc.detalhe, request.url.path, exc.regra
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _erro_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Erros do próprio framework (token ausente, corpo ilegível, rota inexistente, método
        # não permitido) saem no mesmo formato da API, e não no `{"detail": ...}` padrão.
        titulo = _TITULOS_HTTP.get(exc.status_code, "Erro")
        return JSONResponse(
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
            content=_payload(
                exc.status_code,
                titulo,
                f"/erros/http-{exc.status_code}",
                str(exc.detail),
                request.url.path,
            ),
        )

    @app.exception_handler(DataError)
    async def _valor_fora_do_intervalo(request: Request, exc: DataError) -> JSONResponse:
        # O banco recusou o valor (inteiro além de 32 bits num id, por exemplo): é entrada
        # inválida, não falha do servidor. A mensagem do driver nunca sai na resposta (NFR-SEG-06).
        logger.warning("Valor fora do intervalo aceito pelo banco em %s", request.url.path)
        return JSONResponse(
            status_code=422,
            content=_payload(
                422,
                "Erro de validação",
                "/erros/validacao",
                "Um valor numérico está fora do intervalo aceito.",
                request.url.path,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _erro_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_payload(
                422,
                "Erro de validação",
                "/erros/validacao",
                "Um ou mais campos são inválidos.",
                request.url.path,
                erros=jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(Exception)
    async def _erro_interno(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erro interno não tratado em %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content=_payload(
                500,
                "Erro interno",
                "/erros/interno",
                "Ocorreu um erro inesperado.",
                request.url.path,
            ),
        )
