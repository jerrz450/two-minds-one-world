from pathlib import Path

DATA_ROOT = Path("/app/data")

def _workspace(agent_id: str) -> Path:

    path = DATA_ROOT / "agents" / agent_id / "workspace"
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o777)
    except PermissionError:
        pass
    return path


def read_file(agent_id: str, name: str) -> dict:
    
    path = _workspace(agent_id) / name

    if not path.exists():
        return {"error": f"'{name}' not found in workspace."}
    return {"name": name, "content": path.read_text(encoding="utf-8")}


def write_file(agent_id: str, name: str, content: str) -> dict:

    path = _workspace(agent_id) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"status": "written", "name": name}


def edit_file(agent_id: str, name: str, old_string: str, new_string: str) -> dict:

    path = _workspace(agent_id) / name
    if not path.exists():
        return {"error": f"'{name}' not found in workspace."}

    content = path.read_text(encoding="utf-8")
    count = content.count(old_string)

    if count == 0:
        return {"error": "old_string not found in file. Read the file first to check exact content."}

    if count > 1:
        return {"error": f"old_string matches {count} locations — add more surrounding context to make it unique."}
    path.write_text(content.replace(old_string, new_string, 1), encoding="utf-8")
    return {"status": "edited", "name": name}
