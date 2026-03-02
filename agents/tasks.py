import asyncio
import os
from celery import signals
from celery_app import app
from agents.loop import AgentLoop


@app.task(name="agents.tasks.run_session")
def run_session(agent_id: str) -> None:
    print(f"[task] starting session for {agent_id}")
    try:
        asyncio.run(AgentLoop(agent_id).run())
    except Exception as e:
        print(f"[task] session error for {agent_id}: {e}")


@signals.worker_ready.connect
def on_worker_ready(sender, **kwargs):
    agent_id = os.getenv("AGENT_ID")
    if agent_id:
        print(f"[startup] triggering first session for {agent_id}")
        run_session.apply_async(args=[agent_id], queue=agent_id, countdown=3)
