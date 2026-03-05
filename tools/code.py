from pathlib import Path

import requests
from config.clients import get_db
from tools.world import get_world_state

EXECUTOR_URL = "http://executor:8080/execute"
EXECUTOR_RUN_FILE_URL = "http://executor:8080/run_file"
DATA_ROOT = Path("/app/data")


def execute_code(agent_id: str, session_id: str, code: str, name: str | None = None, requirements: list[str] | None = None) -> dict:
    """Send code to the executor service and return the result."""
    try:
        resp = requests.post(
            EXECUTOR_URL,
            json={"code": code, "agent_id": agent_id, "name": name, "requirements": requirements, "world_state": get_world_state()},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": 1, "error": "ExecutorUnreachable"}


def _resolve_script_path(agent_id: str, name: str) -> Path | None:
    """Find a script by name in agent workspace or shared workspace."""

    def find_in_dir(directory: Path, name: str) -> Path | None:
        exact = directory / (name if name.endswith(".py") else f"{name}.py")
        if exact.exists():
            return exact
        matches = directory.glob(f"*_{name}.py")
        return max(matches, default=None, key=lambda p: p.stat().st_mtime)

    agent_workspace = DATA_ROOT / "agents" / agent_id / "workspace"
    shared_workspace = DATA_ROOT / "shared" / "workspace"
    return find_in_dir(agent_workspace, name) or find_in_dir(shared_workspace, name)


def list_scripts(agent_id: str, session_id: str) -> dict:
    """List all saved scripts in the agent's workspace."""
    workspace = DATA_ROOT / "agents" / agent_id / "workspace"
    if not workspace.exists():
        return {"scripts": []}
    scripts = sorted(workspace.glob("*.py"), key=lambda p: p.stat().st_mtime)
    return {"scripts": [p.name for p in scripts]}


def run_script(agent_id: str, session_id: str, name: str) -> dict:
    """Run a previously saved script from the agent's workspace by name."""
    script = _resolve_script_path(agent_id, name)
    if not script:
        return {"error": f"No script named '{name}' found. Use list_scripts() to see available scripts."}
    try:
        executor_path = str(script).replace("/app/data/", "/data/")
        resp = requests.post(
            EXECUTOR_RUN_FILE_URL,
            json={"path": executor_path, "agent_id": agent_id, "world_state": get_world_state()},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": 1, "error": "ExecutorUnreachable"}


def deploy_script(agent_id: str, session_id: str, name: str) -> dict:
    """Deploy a script to run automatically every world tick."""
    found_path = _resolve_script_path(agent_id, name)
    if not found_path:
        return {"error": f"No script named '{name}' found. Use list_scripts() to see available scripts."}
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO deployed_scripts (agent_id, script_name, script_path)
                VALUES (%s, %s, %s)
                ON CONFLICT (agent_id) DO UPDATE
                    SET script_name = EXCLUDED.script_name,
                        script_path = EXCLUDED.script_path,
                        deployed_at = NOW()
                """,
                (agent_id, name, str(found_path).replace("/app/data/", "/data/")),
            )
    return {"status": "deployed", "script": name, "runs_every": "world tick (~5 min)"}
