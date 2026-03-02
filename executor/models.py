from pydantic import BaseModel

class ExecRequest(BaseModel):

    code: str
    agent_id: str
    name: str | None = None
    requirements: list[str] | None = None

class RunFileRequest(BaseModel):

    path: str
    agent_id: str

class ExecResponse(BaseModel):

    stdout: str
    stderr: str
    exit_code: int
    script_path: str | None = None
    error: str | None = None