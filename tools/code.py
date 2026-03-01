from pathlib import Path

import requests

EXECUTOR_URL = "http://executor:8080/execute"
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