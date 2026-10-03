from fastapi import FastAPI

from app.api.tecnico import router as tecnico_router
from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.exceptions import registrar_handlers_erro
from app.core.logging import configurar_logging
from app.core.metrics import instrumentar

configurar_logging(get_settings().log_level)

app = FastAPI(title="ITAM API", version="0.1.0")

registrar_handlers_erro(app)
instrumentar(app)
app.include_router(tecnico_router)
app.include_router(api_v1_router, prefix="/api/v1")
