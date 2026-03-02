import json
from psycopg2.extras import execute_values, RealDictCursor
from config.clients import get_db

def write_world_events_batch(events: list[dict]) -> None:
    
    """Insert multiple world events in a single query.
    Each dict must have: cycle_number, event_type, description.
    Optional keys: affected_agent, payload.
    """

    if not events:
        return

    rows = [
        (
            e["cycle_number"],
            e["event_type"],
            e["description"],
            e.get("affected_agent"),
            json.dumps(e.get("payload") or {}),
        )
        for e in events
    ]

    with get_db() as conn:

        with conn.cursor() as cur:
            execute_values(
                cur,
                "INSERT INTO world_events (cycle_number, event_type, description, affected_agent, payload) VALUES %s",
                rows,
            )

def get_recent_world_events(limit: int = 10) -> list[str]:
    
    """Return recent world event descriptions, newest first. Used to populate session_start."""
    
    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT description FROM world_events
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            
    return [r["description"] for r in reversed(rows)]


def write_increment_world_cycle() -> int:

    with get_db() as conn:

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO world_cycles (cycle_number)
                SELECT COALESCE(MAX(cycle_number), 0) + 1
                FROM world_cycles
                RETURNING cycle_number
                """
            )
            return cur.fetchone()[0]
        
