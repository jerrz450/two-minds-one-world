# Pydantic settings that reads from .env file. Everything else imports from here.

from pydantic_settings import BaseSettings, SettingsConfigDict

AGENT_IDS = ["jordan", "marcus", "priya", "zoe", "devon"]

# Per-agent model config — override via .env: JORDAN_MODEL, MARCUS_MODEL_PROVIDER, etc.
_AGENT_DEFAULTS: dict[str, dict] = {
    "jordan": {"model": "gpt-4.1",          "provider": "openai"},
    "marcus": {"model": "gpt-4.1",          "provider": "openai"},
    "priya":  {"model": "qwen/qwen3-32b",   "provider": "groq"},
    "zoe":    {"model": "gpt-4.1",          "provider": "openai"},
    "devon":  {"model": "qwen/qwen3-32b",   "provider": "groq"},
}

class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    OPENAI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None

    LLM_MODEL: str = "gpt-4.1"
    DISTILL_MODEL: str = "gpt-4o-mini"

    # Per-agent overrides (read dynamically in get_agent_llm)
    JORDAN_MODEL: str = _AGENT_DEFAULTS["jordan"]["model"]
    JORDAN_MODEL_PROVIDER: str = _AGENT_DEFAULTS["jordan"]["provider"]

    MARCUS_MODEL: str = _AGENT_DEFAULTS["marcus"]["model"]
    MARCUS_MODEL_PROVIDER: str = _AGENT_DEFAULTS["marcus"]["provider"]

    PRIYA_MODEL: str = _AGENT_DEFAULTS["priya"]["model"]
    PRIYA_MODEL_PROVIDER: str = _AGENT_DEFAULTS["priya"]["provider"]

    ZOE_MODEL: str = _AGENT_DEFAULTS["zoe"]["model"]
    ZOE_MODEL_PROVIDER: str = _AGENT_DEFAULTS["zoe"]["provider"]

    DEVON_MODEL: str = _AGENT_DEFAULTS["devon"]["model"]
    DEVON_MODEL_PROVIDER: str = _AGENT_DEFAULTS["devon"]["provider"]

    MAX_TOKENS: int = 150
    TEMPERATURE: float = 0.7

    DATABASE_URL: str = "postgresql://twominds:changeme@localhost:5433/twominds"
    REDIS_URL: str = "redis://localhost:6379/0"

    AGENT_ID: str = "jordan"
    BUDGET_USD: float = 5.00

    GITHUB_TOKEN: str | None = None
    GITHUB_REPO_OWNER: str = ""
    GITHUB_REPO_NAME: str = ""

settings = Settings()