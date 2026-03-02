from config.clients import get_db
from psycopg2.extras import RealDictCursor

# Points awarded per tool call.
_TOOL_SCORES = {

    # World-building
    "create_artifact":   20,
    "execute_code":      15,
    "update_artifact":   12,

    # Self-improvement
    "edit_constitution": 10,
    "edit_prompt":        8,
    "write_file":         8,
    "edit_file":          6,

    # Collaboration
    "send_message":       6,
    # Research
    "browse_web":         8,
    "fetch_url":          4,
    "web_search":         2,
    # Communication (easy to abuse)
    "write_board":        1,
    # No external effect
    "write_journal":      0,
}

def score_last_cycle_actions(cycle: int) -> list[dict]:
    
    """Score tool_call events since the previous cycle. Inserts rows into agent_scores.
    Returns list of {agent_id, delta, reason} for logging."""

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            # Get the timestamp of the previous cycle to bound the window
            cur.execute(
                "SELECT created_at FROM world_cycles WHERE cycle_number = %s",
                (cycle - 1,),
            )
            row = cur.fetchone()
            since = row["created_at"] if row else None

            # Fetch tool_call events in the window
            if since:
                cur.execute(
                    """
                    SELECT agent_id, payload->>'tool' AS tool
                    FROM events
                    WHERE event_type = 'tool_call' AND created_at > %s
                    """,
                    (since,),
                )

            else:
                cur.execute(
                    "SELECT agent_id, payload->>'tool' AS tool FROM events WHERE event_type = 'tool_call'"
                )

            rows = cur.fetchall()
 
    totals: dict[str, int] = {}

    for r in rows:
        agent = r["agent_id"]
        totals[agent] = totals.get(agent, 0) + _TOOL_SCORES.get(r["tool"], 0)

    # -10 for inactive agents, merge known agents into one comprehension
    score_rows = [
        (agent_id, cycle, totals.get(agent_id, -10), f"cycle {cycle} activity score")
        for agent_id in {"agent_a", "agent_b"} | totals.keys()
    ]

    if score_rows:

        from psycopg2.extras import execute_values

        with get_db() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    "INSERT INTO agent_scores (agent_id, cycle_number, delta, reason) VALUES %s",
                    score_rows,
                )

    return [{"agent_id": a, "delta": d, "reason": f"cycle {cycle} activity score"} for a, d in totals.items()]