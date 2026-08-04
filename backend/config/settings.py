from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "WorldLens AI"
    APP_VERSION: str = "0.1.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # Database
    DATABASE_PATH: str = str(Path(__file__).parent.parent.parent / "data" / "worldlens.db")

    # LLM
    LLM_PROVIDER: str = "claude"
    LLM_MODEL: str = "claude-haiku-4-5-20251001"
    LLM_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1000

    # Collection
    COLLECTION_INTERVAL_MINUTES: int = 30
    NEWSAPI_KEY: str = ""
    AUTO_ANALYZE: bool = True   # ✅ 新增自动分析

    # Briefing
    BRIEFING_TOP_N: int = 10

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> Settings:
    return Settings()
