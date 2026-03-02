from config.clients import get_db
from psycopg2.extras import RealDictCursor

def decay_artifacts(amount: int = 10) -> tuple[list[str], list[dict]]:

    """Reduce health of all artifacts by amount. Delete those at 0.
    Returns (dead_names, survivors) where survivors is [{name, health}]."""

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE world_artifacts SET health = GREATEST(health - %s, 0) RETURNING name, health",
                (amount,),
            )

            updated = cur.fetchall()
            dead = [r["name"] for r in updated if r["health"] == 0]
            survivors = [{"name": r["name"], "health": r["health"]} for r in updated if r["health"] > 0]

            if dead:
                cur.execute("DELETE FROM world_artifacts WHERE name = ANY(%s)", (dead,))

    return dead, survivors

