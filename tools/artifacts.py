from psycopg2.extras import RealDictCursor
from config.clients import get_db

def create_artifact(name: str, content: str) -> dict:

    """Create a new world artifact or overwrite an existing one."""

    with get_db() as conn:

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO world_artifacts (name, content)
                VALUES (%s, %s)
                ON CONFLICT (name) DO UPDATE
                    SET content = EXCLUDED.content, last_maintained_at = NOW()
                RETURNING id
                """,
                (name, content),
            )
            row = cur.fetchone()

    return {"status": "created", "id": str(row[0])}


def read_artifact(name: str) -> dict:
    
    """Read a world artifact by name."""

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT name, content, health, created_at FROM world_artifacts WHERE name = %s",
                (name,),
            )

            row = cur.fetchone()

    if not row:
        return {"error": f"No artifact named '{name}'"}
    
    return {"name": row["name"], "content": row["content"], "health": row["health"]}

def update_artifact(name: str, content: str) -> dict:

    """Update an existing artifact's content. Also restores 10 health points."""

    with get_db() as conn:

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE world_artifacts
                SET content = %s, last_maintained_at = NOW(), health = LEAST(health + 10, 100)
                WHERE name = %s
                """,
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

    """List all world artifacts with name, health, and creation time."""

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT name, health, created_at FROM world_artifacts ORDER BY created_at ASC"
            )
            rows = cur.fetchall()

    return [      
        {"name": r["name"], "health": r["health"], "created_at": r["created_at"].isoformat()}
        for r in rows
    ]
