from openai import OpenAI
from config.clients import get_db
from config.settings import settings
from psycopg2.extras import RealDictCursor


_NARRATOR_SYSTEM = (
    "You are the silent narrator of a shared world inhabited by two AI agents. "
    "Each world cycle you observe what actually happened and write a brief atmospheric event — "
    "something the agents will read when they next wake up. "
    "Be vivid and concise. Do not invent facts. Do not declare a winner. "
    "Write 1-3 sentences only. Output plain text, no formatting."
)

_NARRATOR_USER = """\
World cycle {cycle} just completed. Here is what happened:

- Artifacts in existence: {artifact_count}
- Artifacts that perished this cycle: {dead}
- Artifacts with critically low health (≤30): {critical}
- Board posts this cycle: {board_posts}
- Scores this cycle: {scores}
- Cumulative scores so far: {cumulative}

Write a brief world event that captures the mood of this cycle.
"""

def _call_narrator(prompt: str) -> str | None:

    try:

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.DISTILL_MODEL,
            messages=[
                {"role": "system", "content": _NARRATOR_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            max_tokens=250,
            temperature=0.8,
        )

        return response.choices[0].message.content.strip()
        
    except Exception as e:
        
        print(f"[narrator] error: {e}")
        return None

def _read_world_state(cycle: int) -> dict:

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute("SELECT COUNT(*) AS cnt FROM world_artifacts")
            artifact_count = cur.fetchone()["cnt"]

            cur.execute(
                "SELECT created_at FROM world_cycles WHERE cycle_number = %s",
                (cycle - 1,),
            )

            row = cur.fetchone()
            since = row["created_at"] if row else None

            if since:
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM board_posts WHERE created_at > %s",
                    (since,),
                )

            else:
                cur.execute("SELECT COUNT(*) AS cnt FROM board_posts")

            board_posts = cur.fetchone()["cnt"]

    return {"artifact_count": artifact_count, "board_posts_since_last_cycle": board_posts}

def _get_cumulative_scores(cycle: int) -> dict[str, int]:

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT agent_id, SUM(delta) AS total
                FROM agent_scores
                WHERE cycle_number <= %s
                GROUP BY agent_id
                """,
                (cycle,),
            )

            rows = cur.fetchall()
            
    return {r["agent_id"]: r["total"] for r in rows}


def generate_world_events(
    cycle: int,
    scores: list[dict],
    dead: list[str],
    survivors: list[dict],
) -> list[dict]:
    
    """Call the LLM narrator with all tick facts. Returns event dicts for the batch."""

    state = _read_world_state(cycle) # current artifact count and board posts since last cycle
    cumulative = _get_cumulative_scores(cycle) # Agent score, per each agent

    critical = [a["name"] for a in survivors if a["health"] <= 30]
    score_str = ", ".join(f"{s['agent_id']}: {s['delta']:+d}" for s in scores) or "none"
    cumulative_str = ", ".join(f"{a}: {v:+d}" for a, v in cumulative.items()) or "none"

    prompt = _NARRATOR_USER.format(
        cycle=cycle,
        artifact_count=state["artifact_count"],
        dead=", ".join(dead) if dead else "none",
        critical=", ".join(critical) if critical else "none",
        board_posts=state["board_posts_since_last_cycle"],
        scores=score_str,
        cumulative=cumulative_str,
    )

    narrative = _call_narrator(prompt)

    events = []

    if narrative:
        events.append({
            "cycle_number": cycle,
            "event_type": "narrator",
            "description": narrative,
        })

    # Milestone: factual summary every 10 cycles
    if cycle % 10 == 0:
        events.append({
            "cycle_number": cycle,
            "event_type": "milestone",
            "description": f"Cycle {cycle} reached. Cumulative scores — {cumulative_str}.",
        })

    return events