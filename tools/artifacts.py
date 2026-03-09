from psycopg2.extras import RealDictCursor
from config.clients import get_db


def create_artifact(name: str, content: str) -> dict:

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO world_artifacts (name, content)
                VALUES (%s, %s)
                ON CONFLICT (name) DO UPDATE
                    SET content = EXCLUDED.content, updated_at = NOW()
                RETURNING id
                """,
                (name, content),
            )
            row = cur.fetchone()
    return {"status": "created", "id": str(row[0])}


def read_artifact(name: str) -> dict:

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT name, content FROM world_artifacts WHERE name = %s",
                (name,),
            )
            row = cur.fetchone()

    if not row:
        return {"error": f"No artifact named '{name}'"}
    
    return {"name": row["name"], "content": row["content"]}


def update_artifact(name: str, content: str) -> dict:

    with get_db() as conn:

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE world_artifacts SET content = %s, updated_at = NOW() WHERE name = %s",
                (content, name),
            )
            if cur.rowcount == 0:
                return {"error": f"No artifact named '{name}'"}
            
    return {"status": "updated"}


def artifact(agent_id: str, session_id: str, action: str, name: str, content: str | None = None) -> dict:

    if action == "create":
        return create_artifact(name, content)
    
    elif action == "read":
        return read_artifact(name)
    
    elif action == "update":
        return update_artifact(name, content)
    
    return {"error": "action must be 'create', 'read', or 'update'"}


def list_artifacts() -> list[dict]:

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT name FROM world_artifacts ORDER BY created_at ASC")
            rows = cur.fetchall()
            
    return [{"name": r["name"]} for r in rows]
