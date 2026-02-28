import ast
from datetime import datetime
from pathlib import Path

import black

DATA_ROOT = Path("/data")


def prepare_code(code: str) -> dict:

    """Strip fences, syntax check, format. Returns {code} or {error}."""

    code = _strip_fences(code)

    try:
        ast.parse(code)
    except SyntaxError as e:
        return {"error": f"SyntaxError: {e}"}

    code = _format(code)
    return {"code": code}


def save_script(code: str, agent_id: str, name: str | None) -> Path:
    """Save to data/agents/{agent_id}/workspace/ and return the path."""
    workspace = DATA_ROOT / "agents" / agent_id / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{name}.py" if name else f"{timestamp}.py"
    path = workspace / filename
    path.write_text(code, encoding="utf-8")
    return path


def _strip_fences(code: str) -> str:
    lines = code.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def _format(code: str) -> str:
    try:
        return black.format_str(code, mode=black.Mode())
    except Exception:
        return code
