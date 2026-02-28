import requests

EXECUTOR_URL = "http://executor:8080/execute"


def execute_code(agent_id: str, session_id: str, code: str, name: str | None = None) -> dict:
    """Send code to the executor service and return the result."""
    try:
        resp = requests.post(
            EXECUTOR_URL,
            json={"code": code, "agent_id": agent_id, "name": name},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": 1, "error": "ExecutorUnreachable"}
