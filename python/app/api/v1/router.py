from fastapi import APIRouter

from app.api.v1.routers import (
    ativos,
    auth,
    categorias,
    cenarios,
    compliance,
    fornecedores,
    importacoes,
    indicadores,
    licencas,
    recomendacoes,
    relatorios,
    responsaveis,
    riscos,
    setores,
)
from app.schemas.erro import ErroResponse

# Erros do padrão único (docs/spec/padrao-de-erros.md), documentados em toda rota do contrato.
# O 422 daqui substitui o `HTTPValidationError` que o FastAPI documentaria: a API devolve o
# corpo `ErroResponse` também na validação.
RESPOSTAS_DE_ERRO: dict[int | str, dict] = {
    400: {
        "model": ErroResponse,
        "description": "Corpo da requisição ilegível (JSON ou multipart).",
    },
    401: {"model": ErroResponse, "description": "Sem token válido."},
    403: {"model": ErroResponse, "description": "Perfil sem permissão (FR-015)."},
    404: {"model": ErroResponse, "description": "Recurso inexistente."},
    409: {"model": ErroResponse, "description": "Operação recusada por regra de negócio."},
    422: {"model": ErroResponse, "description": "Payload malformado ou inválido."},
}

router = APIRouter(responses=RESPOSTAS_DE_ERRO)
router.include_router(auth.router)
router.include_router(categorias.router)
router.include_router(fornecedores.router)
router.include_router(setores.router)
router.include_router(responsaveis.router)
router.include_router(ativos.router)
router.include_router(importacoes.router)
router.include_router(licencas.router)
router.include_router(relatorios.router)
router.include_router(compliance.router)
router.include_router(indicadores.router)
router.include_router(riscos.router)
router.include_router(cenarios.router)
router.include_router(recomendacoes.router)
