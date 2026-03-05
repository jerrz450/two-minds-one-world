import requests
from psycopg2.extras import RealDictCursor
from config.clients import get_db
from executor.models import ExecResponse

EXECUTOR_RUN_FILE_URL = "http://executor:8080/run_file"
_OUTPUT_CAP = 500

def run_deployed_scripts(cycle: int) -> list[dict]:

    """Run the most recently deployed script per agent. Returns world events."""

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT agent_id, script_name, script_path
                FROM deployed_scripts
                """
            )
            rows = cur.fetchall()

    if not rows:
        return []

    events = []

    for row in rows:

        agent_id = row["agent_id"]
        script_name = row["script_name"]
        script_path = row["script_path"]

        resp = ExecResponse(**requests.post(
            EXECUTOR_RUN_FILE_URL,
            json={"path": script_path, "agent_id": agent_id},
            timeout=30,
        ).json())

        stdout = resp.stdout.strip()
        stderr = resp.stderr.strip()
        exit_code = resp.exit_code

        last_output = (stderr if exit_code != 0 else stdout)[:_OUTPUT_CAP]
        event_type = "script_error" if exit_code != 0 else "script_output"
        board_content = f"[{script_name}] {last_output or '(no output)'}"

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE deployed_scripts SET last_run_at = NOW(), last_output = %s WHERE agent_id = %s",
                    (last_output, agent_id),
                )
                cur.execute(
                    "INSERT INTO board_posts (agent_id, session_id, content) VALUES (%s, '00000000-0000-0000-0000-000000000000', %s)",
                    (agent_id, board_content),
                )

        events.append({
            "cycle_number": cycle,
            "event_type": event_type,
            "description": f"[{agent_id}] script '{script_name}' posted output to board.",
            "affected_agent": agent_id,
        })

    return events
