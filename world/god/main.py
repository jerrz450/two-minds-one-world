from world.world_main import write_world_events_batch, write_increment_world_cycle
from world.god.artifacts import decay_artifacts
from world.god.scores import score_last_cycle_actions
from world.god.events import generate_world_events
from world.god.injector import inject_asymmetric_messages

def run_tick() -> None:

    cycle = write_increment_world_cycle()
    scores = score_last_cycle_actions(cycle)
    dead, survivors = decay_artifacts()

    events = []

    for name in dead:

        events.append({
            "cycle_number": cycle,
            "event_type": "artifact_decayed",
            "description": f"Artifact '{name}' perished from neglect.",
        })

    for a in survivors:

        if a["health"] <= 30:
            events.append({
                "cycle_number": cycle,
                "event_type": "artifact_warning",
                "description": f"Artifact '{a['name']}' is weakening (health: {a['health']}).",
            })

    events.extend(generate_world_events(cycle, scores, dead, survivors))

    for s in scores:

        events.append({
            "cycle_number": cycle,
            "event_type": "score",
            "affected_agent": s["agent_id"],
            "description": f"{s['agent_id']} scored {s['delta']:+d} points this cycle.",
        })

    events.append({
        "cycle_number": cycle,
        "event_type": "tick",
        "description": f"World tick {cycle} complete. {len(dead)} artifact(s) lost.",
    })

    write_world_events_batch(events)
    inject_asymmetric_messages(cycle)