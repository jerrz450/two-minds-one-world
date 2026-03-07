from psycopg2.extras import RealDictCursor
from config.clients import get_db
from config.settings import _AGENT_DEFAULTS

ALL_AGENTS = list(_AGENT_DEFAULTS.keys())

CHANNELS = {
    'general': {'read': ALL_AGENTS, 'write': ALL_AGENTS},
    'engineering': {'read': ['marcus', 'priya', 'devon'], 'write': ['marcus', 'priya', 'devon']},
    'product': {'read': ['jordan', 'zoe'], 'write': ['jordan', 'zoe']},
    'incidents': {'read': ALL_AGENTS, 'write': ALL_AGENTS},  
}

def write_board(agent_id: str, session_id: str, content: str, channel: str = "general") -> dict:

    """Post a message to the public bulletin board."""

    permissions = CHANNELS[channel].get("write", [])

    if agent_id not in permissions:
        return {"status" : "Access Denied", "post_id" : None, "channel" : channel}
    
    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO board_posts (agent_id, session_id, content, channel)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (agent_id, session_id, content, channel),
            )
            row = cur.fetchone()

    return {"status": "posted", "post_id": str(row["id"]), "channel" : channel}


def read_board(agent_id: str | None = None, channel : str = "general") -> list[dict]:

    """Read all posts on the public bulletin board, newest first."""

    permissions = CHANNELS[channel].get("read", [])

    if agent_id not in permissions:
        return []

    with get_db() as conn:
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, agent_id, channel, content, created_at FROM board_posts WHERE channel = %s ORDER BY created_at ASC",
                (channel,),
            )
            rows = cur.fetchall()

    return [
        {
            "id": str(row["id"]),
            "agent_id": row["agent_id"],
            "channel": row["channel"],
            "content": row["content"],
            "posted_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]
