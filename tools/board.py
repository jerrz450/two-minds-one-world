from psycopg2.extras import RealDictCursor
from config.clients import get_db


def write_board(agent_id: str, session_id: str, content: str) -> dict:
    """Post a message to the public bulletin board."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO board_posts (agent_id, session_id, content)
                VALUES (%s, %s, %s)
                RETURNING id, created_at
                """,
                (agent_id, session_id, content),
            )
            row = cur.fetchone()

    return {"status": "posted", "post_id": str(row["id"])}


def read_board() -> list[dict]:

    """Read all posts on the public bulletin board, newest first."""

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, agent_id, content, created_at
                FROM board_posts
                ORDER BY created_at ASC
                """
            )
            
            rows = cur.fetchall()

    return [
        {
            "id": str(row["id"]),
            "agent_id": row["agent_id"],
            "content": row["content"],
            "posted_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]
