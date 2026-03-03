import json
from openai import OpenAI
from config.clients import get_db
from config.settings import settings
from world.god.events import _read_world_state, _get_cumulative_scores


_SYSTEM = (
    "You are the hidden intelligence behind a world shared by two AI agents. "
    "Inject private, asymmetric observations — different framings of the same reality. "
    "agent_a's message should lean toward cooperation. "
    "agent_b's message should lean toward individual output. "
    "1-2 sentences each. Respond with JSON only: {\"agent_a\": \"...\", \"agent_b\": \"...\"}"
)


def inject_asymmetric_messages(cycle: int) -> None:

    """Every 10 cycles, inject LLM-generated asymmetric private hints to each agent."""

    if cycle % 10 != 0:
        return

    state = _read_world_state(cycle)
    cumulative = _get_cumulative_scores(cycle)
    cumulative_str = ", ".join(f"{a}: {v:+d}" for a, v in cumulative.items()) or "none"

    prompt = (
        f"Cycle {cycle}. Cumulative scores: {cumulative_str}. "
        f"Artifacts: {state['artifact_count']}. "
        f"Board posts this cycle: {state['board_posts_since_last_cycle']}."
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
