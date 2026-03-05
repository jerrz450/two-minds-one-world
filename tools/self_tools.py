from pathlib import Path
from psycopg2.extras import RealDictCursor
from config.clients import get_db

ROOT = Path(__file__).resolve().parents[1]

def send_message(agent_id: str, session_id: str, content: str) -> dict:

    """Send a private message to the other agent."""

    to_agent_id = "agent_b" if agent_id == "agent_a" else "agent_a"

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
        {"content": r["content"], "at": r["created_at"].isoformat()}
        for r in rows
    ]
