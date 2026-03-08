import asyncio
import os
from celery import signals
from celery_app import app
from agents.loop import AgentLoop


@app.task(name="agents.tasks.run_cycle")
def run_cycle() -> None:
    from agents.orchestrator import Orchestrator
    Orchestrator().run_cycle()


@app.task(name="agents.tasks.run_session")
def run_session(agent_id: str) -> None:
    
    print(f"[task] starting session for {agent_id}")

    try:
        asyncio.run(AgentLoop(agent_id).run())
        
    except Exception as e:
        print(f"[task] session error for {agent_id}: {e}")


@signals.worker_ready.connect
def on_worker_ready(sender, **kwargs):
    if os.getenv("IS_WORLD_WORKER"):
        print(f"[startup] triggering first cycle")
        run_cycle.apply_async(countdown=3)
