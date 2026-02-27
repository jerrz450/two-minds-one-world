import json
from psycopg2.extras import RealDictCursor
from config.clients import get_db
from db.models import Event

def log_event(agent_id: str, session_id: str, event_type: str, payload: dict) -> Event:

    """
    Append a single event to the event log. Never updates or deletes — append only.
    event_type: thought | tool_call | tool_result | memory_write | observation | journal
    """

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute(
                """
                INSERT INTO events (agent_id, session_id, event_type, payload)
                VALUES (%s, %s, %s, %s)
                RETURNING id, agent_id, session_id, event_type, payload, created_at
                """,
                (agent_id, session_id, event_type, json.dumps(payload)),
            )

            return Event(**cur.fetchone())


def get_recent_events(agent_id: str, limit: int = 50) -> list[Event]:

    """Return the most recent N events for an agent, oldest first."""

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute(
                """
                SELECT id, agent_id, session_id, event_type, payload, created_at
                FROM (
                    SELECT * FROM events WHERE agent_id = %s
                    ORDER BY created_at DESC LIMIT %s
                ) sub
                ORDER BY created_at ASC
                """,
                (agent_id, limit),
            )

            return [Event(**row) for row in cur.fetchall()]


def get_session_events(session_id: str) -> list[Event]:

    """Return all events for a specific session, in order. Used for replay."""

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, agent_id, session_id, event_type, payload, created_at
                FROM events
                WHERE session_id = %s
                ORDER BY created_at ASC
                """,
                (session_id,),
            )

            return [Event(**row) for row in cur.fetchall()]
