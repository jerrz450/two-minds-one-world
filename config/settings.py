# Pydantic settings that reads from .env file. Everything else imports from here.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    OPENAI_API_KEY: str | None = None

    LLM_MODEL: str = "gpt-4.1"
    DISTILL_MODEL: str = "gpt-4o-mini"

    MAX_TOKENS: int = 150
    TEMPERATURE: float = 0.7

    DATABASE_URL: str = "postgresql://twominds:changeme@localhost:5433/twominds"
    REDIS_URL: str = "redis://localhost:6379/0"

    AGENT_ID: str = "agent_a"


settings = Settings()