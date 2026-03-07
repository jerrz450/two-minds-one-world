import ast
from datetime import datetime
from pathlib import Path

import black

DATA_ROOT = Path("/data")

def _strip_fences(code: str) -> str:

    lines = code.strip().splitlines()

    # Find the first opening fence
    start = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            start = i
            break

    if start is None:
        return "\n".join(lines)

    # Find the closing fence after the opening one
    end = None

    for i in range(start + 1, len(lines)):
        if lines[i].strip() == "```":
            end = i
            break

    if end is None:
        # Unclosed fence — take everything after the opening line
        return "\n".join(lines[start + 1:])

    return "\n".join(lines[start + 1:end])

def _format(code: str) -> str:
    
    try:
        return black.format_str(code, mode=black.Mode())
    
    except Exception:
        return code

def prepare_code(code: str) -> dict:

    """Strip fences, syntax check, format. Returns {code} or {error}."""

    code = _strip_fences(code)

    try:
        ast.parse(code)

    except SyntaxError as e:
        return {"error": f"SyntaxError: {e}"}

    code = _format(code)

    return {"code": code}


def save_requirements(packages: list[str], agent_id: str) -> None:

    """Merge packages into the agent's requirements.txt (no duplicates)."""

    workspace = DATA_ROOT / "agents" / agent_id / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    req_file = workspace / "requirements.txt"
    existing = set(req_file.read_text(encoding="utf-8").splitlines()) if req_file.exists() else set()
    merged = existing | set(p.strip() for p in packages if p.strip())
    
    req_file.write_text("\n".join(sorted(merged)) + "\n", encoding="utf-8")

def save_script(code: str, agent_id: str, name: str | None) -> Path:
    
    """Save to data/agents/{agent_id}/workspace/ and return the path."""

    workspace = DATA_ROOT / "agents" / agent_id / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}.py" if name else f"{timestamp}.py"
    path = workspace / filename
    path.write_text(code, encoding="utf-8")

    return path