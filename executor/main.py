from fastapi import FastAPI

from models import ExecRequest, ExecResponse
from prepare import prepare_code, save_script
from run import run_code

app = FastAPI()


@app.post("/execute", response_model=ExecResponse)
def execute(req: ExecRequest) -> ExecResponse:

    result = prepare_code(req.code)
    if result.get("error"):
        return ExecResponse(stdout="", stderr=result["error"], exit_code=1, error="SyntaxError")

    path = save_script(result["code"], req.agent_id, req.name)
    return run_code(path, req.agent_id)
