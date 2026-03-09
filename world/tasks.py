import os
from celery import signals
from celery_app import app
from world.world_main import write_increment_world_cycle, write_world_events_batch
from world.god.runner import run_deployed_scripts


@app.task(name="world.tasks.world_tick")
def world_tick() -> None:

    print("[world] tick fired")

    cycle = write_increment_world_cycle()
    events = run_deployed_scripts(cycle)
    
    events.append({
        "cycle_number": cycle,
        "event_type": "tick",
        "description": f"World tick {cycle} complete.",
    })
    
    write_world_events_batch(events)
    print("[world] tick complete")


@signals.worker_ready.connect
def on_worker_ready(sender, **kwargs):

    if os.getenv("IS_WORLD_WORKER"):
        print("[startup] triggering first world tick")
        world_tick.apply_async(queue="world", countdown=3)
