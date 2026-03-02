from pathlib import Path

import requests

EXECUTOR_URL = "http://executor:8080/execute"
EXECUTOR_RUN_FILE_URL = "http://executor:8080/run_file"
DATA_ROOT = Path("/app/data")

def execute_code(agent_id: str, session_id: str, code: str, name: str | None = None, requirements: list[str] | None = None) -> dict:

    """Send code to the executor service and return the result."""

    try:
        resp = requests.post(
            EXECUTOR_URL,
            json={"code": code, "agent_id": agent_id, "name": name, "requirements": requirements},
            timeout=30,
        )

        resp.raise_for_status()
        return resp.json()
    
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": 1, "error": "ExecutorUnreachable"}


def list_scripts(agent_id: str, session_id: str) -> dict:

    """List all saved scripts in the agent's workspace."""

    workspace = DATA_ROOT / "agents" / agent_id / "workspace"

    if not workspace.exists():
        return {"scripts": []}

    scripts = sorted(workspace.glob("*.py"), key=lambda p: p.stat().st_mtime)

    return {"scripts": [p.name for p in scripts]}


def run_script(agent_id: str, session_id: str, name: str) -> dict:

    """Run a previously saved script from the agent's workspace by name."""

    workspace = DATA_ROOT / "agents" / agent_id / "workspace"
    matches = sorted(workspace.glob(f"*_{name}.py"), key=lambda p: p.stat().st_mtime)

    if not matches:
        # Try exact filename match too
        exact = workspace / name if name.endswith(".py") else workspace / f"{name}.py"
        if exact.exists():
            matches = [exact]
        else:
            return {"error": f"No script named '{name}' found. Use list_scripts() to see available scripts."}

    script = matches[-1]  # most recent version

    try:
        resp = requests.post(
            EXECUTOR_RUN_FILE_URL,
            json={"path": str(script), "agent_id": agent_id},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": 1, "error": "ExecutorUnreachable"}