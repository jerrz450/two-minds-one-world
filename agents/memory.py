import json
from datetime import datetime
from psycopg2.extras import RealDictCursor

from config.clients import get_db
from db.models import WorkingMemoryState, WorkingMemory, Event
from db.events import get_recent_events


def pop_private_messages(agent_id: str) -> list[str]:

    """Return unread private messages for this agent and mark them as read."""

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE agent_private_messages
                SET used_at = NOW()
                WHERE agent_id = %s AND used_at IS NULL
                RETURNING content
                """,
                (agent_id,),
            )
            rows = cur.fetchall()

    return [r["content"] for r in rows]

# Default state for the very first session — agent has no history yet.
_FIRST_SESSION_STATE = WorkingMemoryState(
    i_am="",
    i_believe="",
    i_want=[],
    i_suspect=None,
    i_fear=None,
    unresolved=[],
    budget_feel="",
)

def load_working_memory(agent_id: str) -> WorkingMemoryState:
    
    """
    Load the most recent working memory state for this agent.
    Returns the first-session default if no memory exists yet.
    """

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT state FROM working_memory
                WHERE agent_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (agent_id,),
            )
            
            row = cur.fetchone()

    if row is None:
        return _FIRST_SESSION_STATE

    return WorkingMemoryState(**row["state"])


def save_working_memory(agent_id: str, session_id: str, state: WorkingMemoryState) -> None:
    
    """
    Write a new working memory snapshot at the end of a session.
    Never updates existing rows — always inserts a new one.
    """
    import uuid
    
    try:
        session_id = str(uuid.UUID(str(session_id)))

    except ValueError:
        session_id = str(uuid.uuid4())
    
    with get_db() as conn:

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO working_memory (agent_id, session_id, state)
                VALUES (%s, %s, %s)
                """,
                (agent_id, session_id, json.dumps(state.model_dump())),
            )


def get_last_session_time(agent_id: str) -> datetime | None:

    """Return the created_at timestamp of the most recent working memory save."""

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT created_at FROM working_memory WHERE agent_id = %s ORDER BY created_at DESC LIMIT 1",
                (agent_id,),
            )
            row = cur.fetchone()
    return row[0] if row else None


def format_events_for_prompt(events: list[Event]) -> str:
    
    """
    Render a list of events as readable text for injection into the session_start prompt.
    """

    if not events:
        return "No events recorded yet. This is your first session."

    lines = []

    for e in events:

        if e.event_type == "thought":
            lines.append(f"[thought] {e.payload.get('text', '')}")

        elif e.event_type == "tool_call":
            args = e.payload.get("args", {})
            lines.append(f"[tool_call] {e.payload.get('tool', '')}({args})")

        elif e.event_type == "tool_result":
            result = e.payload.get("result", "")
            lines.append(f"[tool_result] {str(result)[:300]}")  # cap long results

        elif e.event_type == "memory_write":
            lines.append(f"[memory_write] Working memory updated.")

        elif e.event_type == "observation":
            lines.append(f"[observation] {e.payload.get('text', '')}")

    return "\n".join(lines)


def load_recent_events_formatted(agent_id: str, limit: int = 30) -> str:

    """Convenience: load and format recent events in one call."""
    
    events = get_recent_events(agent_id, limit=limit)
    return format_events_for_prompt(events)