from contextlib import contextmanager
from openai import AsyncOpenAI
from psycopg2.pool import ThreadedConnectionPool
from redis import Redis

from config.settings import settings


# --- OpenAI (narrator / distill) ---

_openai: AsyncOpenAI | None = None

def get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai


# --- Groq (agent LLMs) ---

_groq: AsyncOpenAI | None = None

def get_groq() -> AsyncOpenAI:
    global _groq
    if _groq is None:
        _groq = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    return _groq


def get_agent_llm(agent_id: str) -> tuple[AsyncOpenAI, str]:

    key = agent_id.upper()
    model = getattr(settings, f"{key}_MODEL", settings.LLM_MODEL)
    provider = getattr(settings, f"{key}_MODEL_PROVIDER", "openai")

    print(f"[{agent_id}] model={model} provider={provider}")

    client = get_openai() if provider == "openai" else get_groq()

    return client, model

# --- Postgres ---

_pool: ThreadedConnectionPool | None = None

def get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=settings.DATABASE_URL)
    return _pool

@contextmanager
def get_db():
    
    conn = get_pool().getconn()

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        get_pool().putconn(conn)

# --- Redis ---
def get_redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)
