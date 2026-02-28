from config.clients import get_db
from config.settings import settings

# USD per 1M tokens: (input, output)
MODEL_COSTS: dict[str, tuple[float, float]] = {
    "gpt-4.1":     (2.00,  8.00),
    "gpt-4o":      (2.50, 10.00),
    "gpt-4o-mini": (0.15,  0.60),
}

def _current_balance() -> float:

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT balance_after FROM budget_ledger ORDER BY created_at DESC LIMIT 1")
            row = cur.fetchone()
            return float(row[0]) if row else settings.BUDGET_USD

def log_cost(agent_id: str, session_id: str, model: str, usage, label: str | None = None) -> float:

    """Insert a budget_ledger row for one API call. Returns cost in USD."""

    input_per_m, output_per_m = MODEL_COSTS.get(model, (2.00, 8.00))
    cost = (usage.prompt_tokens * input_per_m + usage.completion_tokens * output_per_m) / 1_000_000
    balance = _current_balance() - cost

    with get_db() as conn:

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO budget_ledger
                    (agent_id, session_id, tokens_in, tokens_out, tool_name, cost_usd, balance_after)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (agent_id, session_id, usage.prompt_tokens, usage.completion_tokens, label, cost, balance),
            )

    return cost
