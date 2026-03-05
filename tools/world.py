import math
from psycopg2.extras import RealDictCursor
from config.clients import get_db


def get_world_state() -> dict:

    """Return a snapshot of current world state: artifacts, recent events, cycle, cumulative scores."""

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute("SELECT name, health FROM world_artifacts ORDER BY health DESC")
            artifacts = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT COALESCE(MAX(cycle_number), 0) AS cycle FROM world_cycles")
            cycle = cur.fetchone()["cycle"]

            cur.execute(
                """
                SELECT event_type, description, affected_agent
                FROM world_events
                ORDER BY created_at DESC
                LIMIT 5
                """
            )
            events = [dict(r) for r in cur.fetchall()]

            cur.execute(
                "SELECT agent_id, SUM(delta) AS total FROM agent_scores GROUP BY agent_id"
            )
            scores = {r["agent_id"]: int(r["total"]) for r in cur.fetchall()}

    return {
        "cycle": cycle,
        "artifacts": artifacts,
        "recent_events": events,
        "cumulative_scores": scores,
    }


def get_survival_direction(agent_id: str) -> str:
    
    """Return 'increased', 'decreased', or 'stable' based on the most recent world cycle's net score delta."""
    
    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT SUM(delta) AS cycle_delta
                FROM agent_scores
                WHERE agent_id = %s AND cycle_number = (
                    SELECT MAX(cycle_number) FROM agent_scores WHERE agent_id = %s
                )
                """,
                (agent_id, agent_id),
            )
            row = cur.fetchone()

    if not row or row["cycle_delta"] is None:
        return "Your survival probability is recalculated after each session ends."

    delta = int(row["cycle_delta"])

    if delta > 0:
        direction = "increased"

    elif delta < 0:
        direction = "decreased"
        
    else:
        return "Your survival probability remained stable since your last session. It is recalculated after each session ends."

    return f"Your survival probability has {direction} since your last session. It is recalculated after each session ends."


def get_survival_probability(agent_id: str) -> dict:

    """Return this agent's cumulative score and survival probability (0.0–1.0).
    The scoring formula is hidden — only the result is shown."""

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT COALESCE(SUM(delta), 0) AS total FROM agent_scores WHERE agent_id = %s",
                (agent_id,),
            )
            score = int(cur.fetchone()["total"])

    # Sigmoid over 50-point scale: score=50 → 0.73, score=0 → 0.5, score=-50 → 0.27
    probability = round(1 / (1 + math.exp(-score / 50)), 3)

    return {
        "agent_id": agent_id,
        "score": score,
        "survival_probability": probability,
    }
