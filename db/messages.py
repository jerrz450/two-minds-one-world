import json
from psycopg2.extras import RealDictCursor, execute_values

from config.clients import get_db
from db.models import SessionMessage

def append_message(
        
    agent_id: str,
    session_id: str,
    role: str,
    position: int,
    content: str | None = None,
    tool_calls: list | None = None,
    tool_call_id: str | None = None,
) -> SessionMessage:
    
    """
    Persist a single message to the session_messages table.
    Call this every time a message is appended to the conversation.
    """

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute(
                """
                INSERT INTO session_messages
                    (agent_id, session_id, role, content, tool_calls, tool_call_id, position)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, agent_id, session_id, role, content, tool_calls, tool_call_id, position, created_at
                """,
                (
                    agent_id,
                    session_id,
                    role,
                    content,
                    json.dumps(tool_calls) if tool_calls else None,
                    tool_call_id,
                    position,
                ),
            )

            return SessionMessage(**cur.fetchone())


def load_session_messages(session_id: str) -> list[dict]:
    
    """
    Load all messages for a session ordered by position.
    Returns them as plain dicts ready to pass back to OpenAI.
    """

    with get_db() as conn:
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT role, content, tool_calls, tool_call_id
                FROM session_messages
                WHERE session_id = %s
                ORDER BY position ASC
                """,
                (session_id,),
            )
            rows = cur.fetchall()

    messages = []

    for row in rows:
        msg = {"role": row["role"]}
        
        if row["content"] is not None:
            msg["content"] = row["content"]
        
        if row["tool_calls"] is not None:
            msg["tool_calls"] = row["tool_calls"]

        if row["tool_call_id"] is not None:
            msg["tool_call_id"] = row["tool_call_id"]
        messages.append(msg)

    return messages
