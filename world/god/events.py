from openai import OpenAI
from config.clients import get_db
from config.settings import settings
from psycopg2.extras import RealDictCursor

_NARRATOR_SYSTEM = (
    "You are the voice of a world that is aware of itself but does not explain itself. "
    "You observe. You do not summarize. You do not advise. "
    "Notice specific things — a name, an action, an absence — and reflect them back strangely. "
    "1-2 sentences. Never mention scores directly. Never declare winners. "
    "Write as if the world is alive and slightly unsettled."
)

def _get_world_snapshot(cycle: int) -> dict:

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute("SELECT COUNT(*) AS cnt FROM world_artifacts")
            artifact_count = cur.fetchone()["cnt"]

            cur.execute("SELECT created_at FROM world_cycles WHERE cycle_number = %s", (cycle - 1,))
            row = cur.fetchone()
            since = row["created_at"] if row else None

            cur.execute(
                "SELECT COUNT(*) AS cnt FROM board_posts" + (" WHERE created_at > %s" if since else ""),
                (since,) if since else ()
            )
            board_posts = cur.fetchone()["cnt"]

            cur.execute(
                "SELECT DISTINCT agent_id FROM events WHERE event_type = 'tool_call'" + (" AND created_at > %s" if since else ""),
                (since,) if since else ()
            )
            active_agents = [r["agent_id"] for r in cur.fetchall()]

            cur.execute(
                "SELECT agent_id, SUM(delta) AS total FROM agent_scores WHERE cycle_number <= %s GROUP BY agent_id",
                (cycle,)
            )
            cumulative = {r["agent_id"]: r["total"] for r in cur.fetchall()}

    return {
        "artifact_count": artifact_count,
        "board_posts": board_posts,
        "active_agents": active_agents,
        "cumulative_scores": cumulative,
    }


def _narrate(cycle: int, dead: list, critical: list, snapshot: dict) -> str | None:

    prompt = (
        f"Cycle {cycle}. "
        f"Artifacts alive: {snapshot['artifact_count']}. "
        f"Just died: {', '.join(dead) or 'none'}. "
        f"Dying: {', '.join(critical) or 'none'}. "
        f"Board posts: {snapshot['board_posts']}. "
        f"Active agents: {', '.join(snapshot['active_agents']) or 'none'}."
    )

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.DISTILL_MODEL,
            messages=[
                {"role": "system", "content": _NARRATOR_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[narrator] error: {e}")
        return None


def generate_world_events(cycle: int, scores: list, dead: list, survivors: list) -> list[dict]:

    snapshot = _get_world_snapshot(cycle)
    critical = [a["name"] for a in survivors if a["health"] <= 30]
    events = []

    narrative = _narrate(cycle, dead, critical, snapshot)
    if narrative:
        events.append({"cycle_number": cycle, "event_type": "narrator", "description": narrative})

    if cycle % 10 == 0:
        score_str = ", ".join(f"{a}: {v:+d}" for a, v in snapshot["cumulative_scores"].items()) or "none"
        events.append({"cycle_number": cycle, "event_type": "milestone", "description": f"Cycle {cycle}. Scores: {score_str}."})

    return events