import os
from celery import signals
from celery_app import app
from world.god.main import run_tick


@app.task(name="world.tasks.world_tick")
def world_tick() -> None:
    print("[world] tick fired")
    run_tick()
    print("[world] tick complete")


@signals.worker_ready.connect
def on_worker_ready(sender, **kwargs):
    if os.getenv("IS_WORLD_WORKER"):
        
        print("[startup] triggering first world tick")
        world_tick.apply_async(queue="world", countdown=3)
