import os
import socket
import subprocess
from pathlib import Path

from models import ExecResponse, ShellResponse

DATA_ROOT = Path("/data")
TIMEOUT = 30
MEMORY = "128m"
CPUS = "0.5"

def run_shell_command(agent_id: str, command: str) -> ShellResponse:

    executor_container_id = socket.gethostname()

    key = agent_id.upper()
    
    git_name  = os.environ.get(f"GIT_AUTHOR_NAME_{key}", agent_id)
    git_email = os.environ.get(f"GIT_AUTHOR_EMAIL_{key}", f"{agent_id}@startup.dev")

    docker_cmd = [
        "docker", "run", "--rm",
        "--security-opt", "seccomp=/app/seccomp.json",
        "--network", "none",
        "--memory", MEMORY,
        "--cpus", CPUS,
        "--volumes-from", executor_container_id,
        "-e", f"GIT_AUTHOR_NAME={git_name}",
        "-e", f"GIT_AUTHOR_EMAIL={git_email}",
        "--workdir", "/repo",
        "python:3.12-slim",
        "sh", "-c", command,
    ]

    try:

        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=TIMEOUT)

        return ShellResponse(
            stdout=result.stdout[:4000],
            stderr=result.stderr[:2000],
            exit_code=result.returncode,
        )

    except subprocess.TimeoutExpired:
        return ShellResponse(stdout="", stderr="Execution timed out.", exit_code=1, timed_out=True)

    except Exception as e:
        return ShellResponse(stdout="", stderr=str(e), exit_code=1)

def run_code(script_path: Path, agent_id: str) -> ExecResponse:

    """Run script in an ephemeral Docker container with workspace volumes mounted."""

    agent_workspace = DATA_ROOT / "agents" / agent_id / "workspace"
    req_file = agent_workspace / "requirements.txt"
    executor_container_id = socket.gethostname()

    key = agent_id.upper()
    git_name  = os.environ.get(f"GIT_AUTHOR_NAME_{key}", agent_id)
    git_email = os.environ.get(f"GIT_AUTHOR_EMAIL_{key}", f"{agent_id}@startup.dev")

    if req_file.exists():
        entrypoint = f"pip install -q -r {agent_workspace}/requirements.txt && python {script_path}"
    else:
        entrypoint = f"python {script_path}"

    cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", MEMORY,
        "--cpus", CPUS,
        "--volumes-from", executor_container_id,
        "-e", f"GIT_AUTHOR_NAME={git_name}",
        "-e", f"GIT_AUTHOR_EMAIL={git_email}",
        "--workdir", str(agent_workspace),
        "python:3.12-slim",
        "sh", "-c", entrypoint,
    ]

    try:
        # runs the command, captures output as a string, kills process if run takes more than TIMEOUT
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)

        # on success, it returns this object with stdout limited to 4000 chars, stderr (errors) ect.
        return ExecResponse(
            stdout= result.stdout[:4000],
            stderr= result.stderr[:2000],
            exit_code= result.returncode,
            script_path= str(script_path.relative_to(DATA_ROOT)),
        )

    except subprocess.TimeoutExpired:
        return ExecResponse(stdout="", stderr="Execution timed out.", exit_code=1, error="Timeout")

    except Exception as e:
        return ExecResponse(stdout="", stderr=str(e), exit_code=1, error="ExecutorError")