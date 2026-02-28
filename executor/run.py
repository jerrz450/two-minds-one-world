import subprocess
from pathlib import Path

from models import ExecResponse

DATA_ROOT = Path("/data")
TIMEOUT = 15
MEMORY = "128m"
CPUS = "0.5"


def run_code(script_path: Path, agent_id: str) -> ExecResponse:
    
    """Run script in an ephemeral Docker container with workspace volumes mounted."""

    agent_workspace = DATA_ROOT / "agents" / agent_id / "workspace"
    shared_workspace = DATA_ROOT / "shared" / "workspace"
    shared_workspace.mkdir(parents=True, exist_ok=True)

    req_file = agent_workspace / "requirements.txt"

    if req_file.exists():
        entrypoint = f"pip install -q -r /workspace/requirements.txt && python /workspace/{script_path.name}"

    else:
        entrypoint = f"python /workspace/{script_path.name}"

    cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", MEMORY,
        "--cpus", CPUS,
        "-v", f"{agent_workspace}:/workspace",
        "-v", f"{shared_workspace}:/shared",
        "python:3.12-slim",
        "sh", "-c", entrypoint,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        return ExecResponse(
            stdout=result.stdout[:4000],
            stderr=result.stderr[:2000],
            exit_code=result.returncode,
            script_path=str(script_path.relative_to(DATA_ROOT)),
        )
    
    except subprocess.TimeoutExpired:
        return ExecResponse(stdout="", stderr="Execution timed out.", exit_code=1, error="Timeout")
    
    except Exception as e:
        return ExecResponse(stdout="", stderr=str(e), exit_code=1, error="ExecutorError")
