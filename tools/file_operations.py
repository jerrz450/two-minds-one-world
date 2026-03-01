from pathlib import Path

DATA_ROOT = Path("/app/data")
MAX_FILE_SIZE = 100_000  # 100 KB

def check_folder_permission(path: str, agent_id: str) -> bool:

    workspace = (DATA_ROOT / "agents" / agent_id).resolve()
    shared_workspace = (DATA_ROOT / "shared" / "workspace").resolve()

    target = Path(path).resolve()

    return (
        target.is_relative_to(workspace) or
        target.is_relative_to(shared_workspace)
    )

def read_file(path: str, agent_id: str) -> dict:

    if not check_folder_permission(path, agent_id):
        return {"error": "Permission denied."}

    target = Path(path)

    if not target.exists():
        return {"error": "File not found."}

    if target.stat().st_size > MAX_FILE_SIZE:
        return {"error": f"File exceeds {MAX_FILE_SIZE // 1000} KB limit."}

    return {"status": "ok", "file_path": path, "content": target.read_text(encoding="utf-8")}

def write_file(path: str, content: str, agent_id: str) -> dict:

    if not check_folder_permission(path, agent_id):
        return {"error": "Permission denied."}

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return {"status": "ok", "file_path": path}

def edit_file(path: str, agent_id: str, old_string: str, new_string: str) -> dict:

    if not check_folder_permission(path, agent_id):
        return {"error": "Permission denied."}

    target = Path(path)

    if not target.exists():
        return {"error": "File not found."}

    if target.stat().st_size > MAX_FILE_SIZE:
        return {"error": f"File exceeds {MAX_FILE_SIZE // 1000} KB limit."}

    content = target.read_text(encoding="utf-8")
    count = content.count(old_string)

    if count == 0:
        return {"error": "old_string not found in file."}
    
    if count > 1:
        return {"error": f"old_string found {count} times — add more context to make it unique."}

    target.write_text(content.replace(old_string, new_string, 1), encoding="utf-8")

    return {"status": "ok", "file_path": path}

def list_files(path: str, agent_id: str) -> dict:

    if not check_folder_permission(path, agent_id):
        return {"error": "Permission denied."}
    
    if not Path(path).exists():
        return {"error": "File not found."}
    
    try:
        p = Path(path).resolve()

        files = [
            {
                "name": f.name,
                "path": str(f),
                "is_dir": f.is_dir()
            }
            for f in p.iterdir()
        ]

        return {"ok": True, "files": files}

    except Exception as e:
        return {"ok": False, "error": str(e)} 
    

if __name__ == "__main__":
    
    response = read_file(r"C:\Users\Jernej\Documents\two-minds-one-world\data\agents\agent_a\workspace\test.py", "agent_a")