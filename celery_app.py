import os
from celery import Celery
from config.settings import AGENT_IDS

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
SESSION_INTERVAL = int(os.getenv("SESSION_INTERVAL", "14400"))
WORLD_TICK_INTERVAL = int(os.getenv("WORLD_TICK_INTERVAL", "14400"))

app = Celery(
    "twominds",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["agents.tasks", "world.tasks"],
)

# Stagger agent sessions: jordan first, devon last — each offset by SESSION_INTERVAL/N
_stagger = SESSION_INTERVAL // len(AGENT_IDS)

_beat_schedule = {
    "world-tick": {
        "task": "world.tasks.world_tick",
        "schedule": WORLD_TICK_INTERVAL,
        "options": {"queue": "world"},
    },
}

for i, agent_id in enumerate(AGENT_IDS):
    _beat_schedule[f"session-{agent_id}"] = {
        "task": "agents.tasks.run_session",
        "schedule": SESSION_INTERVAL,
        "args": [agent_id],
        "options": {"queue": agent_id, "countdown": i * _stagger},
    }

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule=_beat_schedule,
)