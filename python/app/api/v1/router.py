from fastapi import APIRouter

from app.api.v1.routers import (
    ativos,
    auth,
    categorias,
    compliance,
    fornecedores,
    importacoes,
    indicadores,
    licencas,
    relatorios,
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
router.include_router(licencas.router)
router.include_router(relatorios.router)
router.include_router(compliance.router)
router.include_router(indicadores.router)
