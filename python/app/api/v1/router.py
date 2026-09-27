from fastapi import APIRouter

from app.api.v1.routers import (
    ativos,
    auth,
    categorias,
    fornecedores,
    importacoes,
    responsaveis,
    setores,
)

router = APIRouter()
router.include_router(auth.router)
router.include_router(categorias.router)
router.include_router(fornecedores.router)
router.include_router(setores.router)
router.include_router(responsaveis.router)
router.include_router(ativos.router)
router.include_router(importacoes.router)
