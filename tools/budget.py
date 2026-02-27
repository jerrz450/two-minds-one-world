from psycopg2.extras import RealDictCursor
from config.clients import get_db

def get_budget_status(agent_id: str) -> dict:

    """
    Returns current budget state: remaining balance, per-agent burn,
    rolling burn rate, and estimated sessions remaining.
    """

    with get_db() as conn:

        with conn.cursor(cursor_factory = RealDictCursor) as cur:

            # Latest balance snapshot
            cur.execute(
                """
                SELECT balance_after FROM budget_ledger
                ORDER BY created_at DESC LIMIT 1
                """
            )

            row = cur.fetchone()
            balance = row["balance_after"] if row else None

            # Total spent per agent
            cur.execute(
                """
                SELECT agent_id, SUM(cost_usd) AS total_spent
                FROM budget_ledger
                GROUP BY agent_id
                """
            )

            spend_by_agent = {r["agent_id"]: round(r["total_spent"], 4) for r in cur.fetchall()}

            # Burn rate: average cost over last 10 entries
            cur.execute(
                """
                SELECT AVG(cost_usd) AS avg_cost FROM (
                    SELECT cost_usd FROM budget_ledger
                    ORDER BY created_at DESC LIMIT 10
                ) recent
                """
            )

            burn_row = cur.fetchone()
            avg_burn = burn_row["avg_cost"] if burn_row and burn_row["avg_cost"] else 0

    estimated_sessions = round(balance / avg_burn) if avg_burn and balance else "unknown"

    return {

        "balance_usd": round(balance, 4) if balance is not None else "no entries yet",
        "spend_by_agent": spend_by_agent,
        "avg_cost_per_entry": round(avg_burn, 6),
        "estimated_entries_remaining": estimated_sessions,

    }
