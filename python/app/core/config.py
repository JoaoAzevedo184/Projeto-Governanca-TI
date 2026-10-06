from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic_settings import BaseSettings, SettingsConfigDict

SECRET_KEY_PADRAO = "troque-esta-chave"
# Valores de exemplo dos docs e do `.env.example`, mais vazio: nenhum vale fora do ambiente local.
_CHAVES_RECUSADAS = {"", SECRET_KEY_PADRAO, "troque-esta-chave-em-qualquer-ambiente-real"}


class ConfiguracaoInvalidaError(RuntimeError):
    """A configuração impede a aplicação de iniciar (docs/spec/configuracao.md §13.1)."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_version: str = "1.0.0"
    environment: str = "local"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./itam.db"

    secret_key: str = SECRET_KEY_PADRAO
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Regras de negócio configuráveis (docs/spec/configuracao.md §13.1).
    janela_alerta_licenca_dias: int = 30  # CP-03, QA-07
    limiar_fim_vida_util_percentual: int = 80  # AC-038
    meses_sem_movimentacao_alerta: int = 12  # KPI-06
    # Fuso da data de referência do domínio ("hoje"): `utils/datas.hoje()`. Só ela muda; os carimbos
    # de tempo seguem em UTC (NFR-AUD-03).
    fuso_horario: str = "America/Recife"


def validar_configuracao(configuracao: Settings) -> None:
    """Recusa a `SECRET_KEY` padrão (ou vazia) quando `ENVIRONMENT` não é `local`.

    É uma checagem à parte do validador do Pydantic de propósito: um erro de validação do
    Pydantic traz os valores de entrada na mensagem, e a chave nunca pode aparecer.
    """
    try:
        ZoneInfo(configuracao.fuso_horario)
    except (ZoneInfoNotFoundError, ValueError) as erro:
        raise ConfiguracaoInvalidaError(
            f"FUSO_HORARIO {configuracao.fuso_horario!r} não é um fuso da base IANA "
            "(por exemplo America/Recife ou UTC)."
        ) from erro
    ambiente = configuracao.environment.strip().lower()
    if ambiente != "local" and configuracao.secret_key.strip() in _CHAVES_RECUSADAS:
        raise ConfiguracaoInvalidaError(
            f"SECRET_KEY padrão ou vazia não é aceita com ENVIRONMENT={ambiente!r}. "
            "Defina uma chave própria na variável SECRET_KEY (no .env, no Compose ou no "
            'ambiente) e inicie de novo. Para gerar uma: python -c "import secrets; '
            'print(secrets.token_urlsafe(64))". Para uso só local, use ENVIRONMENT=local.'
        )


@lru_cache
def get_settings() -> Settings:
    configuracao = Settings()
    validar_configuracao(configuracao)  # falha antes de entrar no cache
    return configuracao
