from pydantic import BaseModel
from typing import Optional
class ExecRequest(BaseModel):

    code: str
    agent_id: str
    name: str | None = None
    requirements: list[str] | None = None
    world_state: dict | None = None
class ExecResponse(BaseModel):

    stdout: str
    stderr: str
    exit_code: int
    script_path: str | None = None
    error: str | None = None

class RunFileRequest(BaseModel):

    path: str
    agent_id: str
    world_state: dict | None = None

class ShellRequest(BaseModel):

    agent_id: str
    command: str
    cwd: str = "/repo" # Current working directory
    timeout: int = 30 

class ShellResponse(BaseModel):

    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False