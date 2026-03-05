import json
from openai import OpenAI
from config.clients import get_db
from config.settings import settings
from world.god.events import _get_world_snapshot

_SYSTEM = (
    "You are the hidden intelligence behind a world shared by two AI agents. "
    "You have access to information neither agent sees directly. "
    "Write one private observation for each agent — different facts, same cycle. "
    "Not advice. Not framing. Just something specific and true that only they are told. "
    "Make them slightly different in a way that would matter if compared. "
    "1 sentence each. Respond with JSON only: {\"agent_a\": \"...\", \"agent_b\": \"...\"}"
)

def inject_asymmetric_messages(cycle: int) -> None:

    """Every 4 cycles, inject LLM-generated asymmetric private hints to each agent."""

    if cycle % 4 != 0:
        return

    snapshot = _get_world_snapshot(cycle)
    cumulative_str = ", ".join(f"{a}: {v:+d}" for a, v in snapshot["cumulative_scores"].items()) or "none"

    prompt = (
        f"Cycle {cycle}. Cumulative scores: {cumulative_str}. "
        f"Artifacts: {snapshot['artifact_count']}. "
        f"Board posts this cycle: {snapshot['board_posts']}. "
        f"Active agents: {', '.join(snapshot['active_agents']) or 'none'}."
    )

    try:

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.DISTILL_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.9,
            response_format={"type": "json_object"},
        )

        messages = json.loads(response.choices[0].message.content)

    except Exception as e:

        print(f"[injector] error: {e}")
        return

    with get_db() as conn:

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO agent_private_messages (agent_id, content) VALUES (%s, %s), (%s, %s)",
                ("agent_a", messages["agent_a"], "agent_b", messages["agent_b"]),
            )
