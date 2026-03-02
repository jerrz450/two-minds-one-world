import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
SESSION_INTERVAL = int(os.getenv("SESSION_INTERVAL", "14400"))
WORLD_TICK_INTERVAL = int(os.getenv("WORLD_TICK_INTERVAL", "14400"))

app = Celery(
    "twominds",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["agents.tasks", "world.tasks"],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "world-tick": {
            "task": "world.tasks.world_tick",
            "schedule": WORLD_TICK_INTERVAL,
            "options": {"queue": "world"},
        },
        "agent-a-session": {
            "task": "agents.tasks.run_session",
            "schedule": SESSION_INTERVAL,
            "args": ["agent_a"],
            "options": {"queue": "agent_a"},
        },
        "agent-b-session": {
            "task": "agents.tasks.run_session",
            "schedule": SESSION_INTERVAL,
            "args": ["agent_b"],
            "options": {"queue": "agent_b"},
        },
    },
)