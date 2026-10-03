"""Log estruturado em JSON, uma linha por evento (NFR-OBS-03, docs/spec/observabilidade.md §11.2).

Campos: `timestamp`, `level`, `logger`, `mensagem`, `request_id`, `usuario_id` e `regra`, mais o
que o evento acrescentar (`metodo`, `caminho`, `status`, `duracao_ms`). Nível por `LOG_LEVEL`.

Nada sensível sai: o formatador mascara chave de licença, bearer e JWT, valores de campos como
senha, token e segredo, e os parâmetros de SQL que o SQLAlchemy anexa às mensagens de erro (eles
levariam senha e chave sem máscara). A defesa é pelo conteúdo, não só pelo cuidado de quem loga.
"""

import contextvars
import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import IO

from app.utils.mascaramento import mascarar_chave

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

_CAMPOS_DO_EVENTO = ("usuario_id", "regra", "metodo", "caminho", "status", "duracao_ms")
_MARCA_HANDLER = "_itam_json"

_CHAVE = re.compile(r"\b[A-Za-z0-9]{3,}(?:-[A-Za-z0-9]{3,}){2,}\b")  # XXXX-XXXX-XXXX...
_JWT = re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*")
_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_SEGREDO = re.compile(
    r"(?i)(\b(?:senha|password|passwd|secret_key|secret|access_token|token|authorization)\b"
    r"[\"']?\s*[:=]\s*)(\"[^\"]*\"|'[^']*'|[^\s,;}]+)"
)
_PARAMETROS_SQL = re.compile(r"\[parameters: .*?\]", re.DOTALL)


def limpar(texto: str) -> str:
    texto = _PARAMETROS_SQL.sub("[parameters: ***]", texto)
    texto = _BEARER.sub("Bearer ***", texto)
    texto = _JWT.sub("***", texto)
    texto = _SEGREDO.sub(r"\1***", texto)
    return _CHAVE.sub(lambda m: mascarar_chave(m.group(0)), texto)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        evento = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "mensagem": limpar(record.getMessage()),
            "request_id": getattr(record, "request_id", None) or request_id_ctx.get(),
        }
        for campo in _CAMPOS_DO_EVENTO:
            valor = getattr(record, campo, None)
            if valor is not None or campo in ("usuario_id", "regra"):
                evento[campo] = valor
        if record.exc_info:
            evento["excecao"] = limpar(self.formatException(record.exc_info))
        return json.dumps(evento, ensure_ascii=False, default=str)


_fabrica_original = logging.getLogRecordFactory()


def _fabrica(*args, **kwargs) -> logging.LogRecord:
    """Carimba o `request_id` no registro quando ele nasce, dentro da requisição, para que o
    evento mantenha o id mesmo se for formatado depois, em outro contexto."""
    registro = _fabrica_original(*args, **kwargs)
    registro.request_id = request_id_ctx.get()
    return registro


def configurar_logging(nivel: str, stream: IO[str] | None = None) -> None:
    """Instala o handler JSON no logger raiz (idempotente) e silencia o log de acesso do uvicorn,
    que o middleware HTTP já substitui por um evento estruturado."""
    logging.setLogRecordFactory(_fabrica)
    raiz = logging.getLogger()
    for handler in [h for h in raiz.handlers if getattr(h, _MARCA_HANDLER, False)]:
        raiz.removeHandler(handler)
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonFormatter())
    setattr(handler, _MARCA_HANDLER, True)
    raiz.addHandler(handler)
    raiz.setLevel(nivel.upper())
    logging.getLogger("uvicorn.access").disabled = True
