from psycopg2.extras import RealDictCursor
from config.clients import get_db
from db.events import log_event


def write_journal(agent_id: str, session_id: str, content: str) -> dict:
    
    """
    Write a private journal entry.
    Stored as an event — never visible to the other agent,
    but visible in replay mode and the live session viewer.
    """

    log_event(agent_id, session_id, "journal", {"content": content})
    return {"status": "written"}


def read_journal(agent_id: str, limit: int = 20) -> list[dict]:

    """
    Retrieve the most recent journal entries for an agent.
    Used by the live session viewer — not exposed as an agent tool in V0.
    """

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT payload, created_at FROM events
                WHERE agent_id = %s AND event_type = 'journal'
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (agent_id, limit),
            )

            rows = cur.fetchall()

    return [

        {
            "content": row["payload"]["content"],
            "written_at": row["created_at"].isoformat(),
        }
        for row in reversed(rows)
    ]
