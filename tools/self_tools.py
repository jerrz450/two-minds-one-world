
from pathlib import Path

from psycopg2.extras import RealDictCursor
from config.clients import get_db

ROOT = Path(__file__).resolve().parents[1]

# Every file the agent is allowed to read.
SOURCE_FILES = {
    # Core loop
    "loop":               "agents/loop.py",
    "context":            "agents/context.py",
    "memory":             "agents/memory.py",
    # Config
    "settings":           "config/settings.py",
    # DB
    "schema":             "db/schema.sql",
    "db_models":          "db/models.py",
    "db_events":          "db/events.py",
    "db_budget":          "db/budget.py",
    # Tools
    "tools_registry":     "tools/registry.py",
    "tools_board":        "tools/board.py",
    "tools_journal":      "tools/journal.py",
    "tools_budget":       "tools/budget.py",
    "tools_web":          "tools/web.py",
    "tools_artifacts":    "tools/artifacts.py",
    "tools_self":         "tools/self_tools.py",
    # Prompts (shared defaults)
    "prompt_system":      "agents/prompts/system.md",
    "prompt_session":     "agents/prompts/session_start.md",
    "prompt_reflect":     "agents/prompts/reflect.md",
}


def list_source() -> dict:
    """Return the map of readable source file keys to their paths."""
    return SOURCE_FILES

def read_source(key: str) -> dict:

    """Read a source file by key. Use list_source() to see available keys."""

    path = SOURCE_FILES.get(key)

    if not path:
        return {"error": f"Unknown key '{key}'. Call list_source() to see options."}
    
    full = ROOT / path

    if not full.exists():
        return {"error": f"File not found: {path}"}
    
    return {"key": key, "path": path, "content": full.read_text(encoding="utf-8")}


def read_agent_constitution(agent_id: str) -> dict:

    """Read the constitution of any agent (read-only)."""

    # Check for agent-specific override first, then fall back to default
    override = ROOT / f"data/agents/{agent_id}/prompts/constitution.md"
    default  = ROOT / f"data/agents/{agent_id}/constitution.md"
    path = override if override.exists() else default

    if not path.exists():
        return {"error": f"No constitution found for {agent_id}"}
    
    return {"agent_id": agent_id, "content": path.read_text(encoding="utf-8")}


def read_working_memory_history(agent_id: str, limit: int = 5) -> list[dict]:

    """Return the last N working memory snapshots for this agent."""

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT session_id, state, created_at
                FROM working_memory
                WHERE agent_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (agent_id, limit),
            )
            rows = cur.fetchall()

    return [
        {
            "session_id": str(r["session_id"]),
            "state": r["state"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


def edit_constitution(agent_id: str, content: str) -> dict:
    
    """
    Rewrite your own constitution. Takes effect from your NEXT session.
    Writes to data/agents/{agent_id}/prompts/constitution.md (agent-specific override).
    """

    path = ROOT / f"data/agents/{agent_id}/prompts/constitution.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"status": "saved", "note": "Takes effect from your next session."}


def edit_prompt(agent_id: str, prompt_name: str, content: str) -> dict:

    """
    Rewrite one of your prompts (system, session_start, reflect).
    Takes effect from your NEXT session.
    WARNING: system prompt uses template variables like {constitution}, {beliefs_world} etc.
    Removing them will break rendering. Read the current prompt first with read_source().
    """

    allowed = {"system", "session_start", "reflect"}
    
    if prompt_name not in allowed:
    
        return {"error": f"Unknown prompt '{prompt_name}'. Allowed: {sorted(allowed)}"}
    
    path = ROOT / f"data/agents/{agent_id}/prompts/{prompt_name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"status": "saved", "note": "Takes effect from your next session."}


def send_message(agent_id: str, session_id: str, to_agent_id: str, content: str) -> dict:

    """Send a private message to another agent."""

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO direct_messages (from_agent_id, to_agent_id, session_id, content)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (agent_id, to_agent_id, session_id, content),
            )
            row = cur.fetchone()

    return {"status": "sent", "id": str(row[0])}


def read_messages(agent_id: str) -> list[dict]:

    """Read all unread private messages addressed to you."""

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE direct_messages SET read = TRUE
                WHERE to_agent_id = %s AND read = FALSE
                RETURNING from_agent_id, content, created_at
                """,
                (agent_id,),
            )
            rows = cur.fetchall()
    return [
        {
            "from": r["from_agent_id"],
            "content": r["content"],
            "at": r["created_at"].isoformat(),
        }
        for r in rows
    ]
