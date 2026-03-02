from fastapi import FastAPI

from pathlib import Path
from models import ExecRequest, RunFileRequest, ExecResponse
from prepare import prepare_code, save_script, save_requirements
from run import run_code

app = FastAPI()

@app.post("/execute", response_model=ExecResponse)
def execute(req: ExecRequest) -> ExecResponse:

    result = prepare_code(req.code)

    if result.get("error"):
        return ExecResponse(stdout="", stderr=result["error"], exit_code=1, error="SyntaxError")

    if req.requirements:
        save_requirements(req.requirements, req.agent_id)

    path = save_script(result["code"], req.agent_id, req.name)

    return run_code(path, req.agent_id)


@app.post("/run_file", response_model=ExecResponse)
def run_file(req: RunFileRequest) -> ExecResponse:

    script_path = Path(req.path)

    if not script_path.exists():
        return ExecResponse(stdout="", stderr=f"File not found: {req.path}", exit_code=1)

    return run_code(script_path, req.agent_id)
