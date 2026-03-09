from psycopg2.extras import RealDictCursor
from config.clients import get_db


def get_world_state() -> dict:
    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            
            cur.execute("SELECT COALESCE(MAX(cycle_number), 0) AS cycle FROM world_cycles")
            cycle = cur.fetchone()["cycle"]
            cur.execute("SELECT name FROM world_artifacts ORDER BY created_at ASC")
            artifacts = [r["name"] for r in cur.fetchall()]

    return {"cycle": cycle, "artifacts": artifacts}
