from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_version: str = "1.0.0"
    environment: str = "local"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./itam.db"

    secret_key: str = "troque-esta-chave"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Regras de negócio configuráveis (docs/spec/configuracao.md §13.1).
    janela_alerta_licenca_dias: int = 30  # CP-03, QA-07
    limiar_fim_vida_util_percentual: int = 80  # AC-038
    meses_sem_movimentacao_alerta: int = 12  # KPI-06


@lru_cache
def get_settings() -> Settings:
    return Settings()
