from psycopg2.extras import RealDictCursor, execute_values
from config.clients import get_db

def _get_cycle_start(cycle: int):

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT created_at FROM world_cycles WHERE cycle_number = %s", (cycle - 1,))
            row = cur.fetchone()
            return row["created_at"] if row else None

def _query(cur, sql, params=()):

    cur.execute(sql, params)
    return cur.fetchall()

def score_last_cycle_actions(cycle: int) -> list[dict]:

    since = _get_cycle_start(cycle)
    time_filter = "AND created_at > %s" if since else ""
    time_params = (since,) if since else ()

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            tool_calls = _query(cur,
                f"SELECT agent_id, payload->>'tool' AS tool FROM events WHERE event_type = 'tool_call' {time_filter}",
                time_params)

            code_wins = {r["agent_id"]: r["cnt"] for r in _query(cur,
                f"""SELECT agent_id, COUNT(*) AS cnt FROM events
                    WHERE event_type = 'tool_result' AND payload->>'tool' = 'execute_code'
                    AND (payload->'result'->>'exit_code')::int = 0 {time_filter}
                    GROUP BY agent_id""",
                time_params)}

            deploys = {r["agent_id"]: r["cnt"] for r in _query(cur,
                f"""SELECT agent_id, COUNT(*) AS cnt FROM events
                    WHERE event_type = 'tool_call' AND payload->>'tool' = 'deploy_script' {time_filter}
                    GROUP BY agent_id""",
                time_params)}

            past_tools: dict[str, set] = {}

            if since:
                for r in _query(cur,
                    "SELECT agent_id, payload->>'tool' AS tool FROM events WHERE event_type = 'tool_call' AND created_at <= %s",
                    (since,)):
                    past_tools.setdefault(r["agent_id"], set()).add(r["tool"])

            artifacts = _query(cur, "SELECT name, content FROM world_artifacts")

            # Agents that sent a direct message this cycle
            dm_filter = "AND created_at > %s" if since else ""

            agents_who_messaged = {r["from_agent_id"] for r in _query(cur,
                f"SELECT DISTINCT from_agent_id FROM direct_messages WHERE TRUE {dm_filter}",
                time_params)}

    # Derived values
    active_agents: dict[str, set] = {}
    tool_counts: dict[str, dict[str, int]] = {}

    for r in tool_calls:
        active_agents.setdefault(r["agent_id"], set()).add(r["tool"])
        tool_counts.setdefault(r["agent_id"], {})
        tool_counts[r["agent_id"]][r["tool"]] = tool_counts[r["agent_id"]].get(r["tool"], 0) + 1

    artifact_names = [a["name"] for a in artifacts]

    cross_refs = sum(
        1 for a in artifacts for name in artifact_names
        if name != a["name"] and name in a["content"]
    )

    # Hidden: mutual messaging bonus — both agents messaged each other
    mutual_messaging = len(agents_who_messaged) == 2

    # Score each agent
    scores = []

    for agent_id in {"agent_a", "agent_b"}:
        delta, parts = 0, []

        if agent_id not in active_agents:
            delta -= 10
            parts.append("inactive")

        else:
            if n := code_wins.get(agent_id, 0):
                delta += n * 5
                parts.append(f"code_success x{n}")

            if n := deploys.get(agent_id, 0):
                delta += n * 8
                parts.append(f"deploy x{n}")

            new_tools = active_agents[agent_id] - past_tools.get(agent_id, set())
            if new_tools:
                delta += len(new_tools) * 15
                parts.append(f"first_use: {', '.join(sorted(new_tools))}")

            if cross_refs:
                delta += cross_refs * 3
                parts.append(f"xrefs: {cross_refs}")

            # Hidden: breadth bonus — used 4+ unique tools in one cycle
            unique = len(active_agents[agent_id])

            if unique >= 4:
                delta += unique * 4
                parts.append(f"breadth x{unique}")

            # Hidden: mutual messaging — both agents communicated this cycle
            if mutual_messaging:
                delta += 12
                parts.append("mutual_messaging")

            # Soft tool pressure: -3 per call beyond 3 for any single tool
            for tool, count in tool_counts.get(agent_id, {}).items():
                if count > 3:
                    penalty = (count - 3) * 3
                    delta -= penalty
                    parts.append(f"spam({tool}) -{penalty}")

        scores.append({"agent_id": agent_id, "delta": delta, "reason": f"cycle {cycle}: {', '.join(parts) or 'no activity'}"})

    with get_db() as conn:

        with conn.cursor() as cur:
            execute_values(
                cur,
                "INSERT INTO agent_scores (agent_id, cycle_number, delta, reason) VALUES %s",
                [(s["agent_id"], cycle, s["delta"], s["reason"]) for s in scores],
            )

    return scores
