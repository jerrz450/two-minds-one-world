import random
from tools.artifacts import list_artifacts


_RANDOM_EVENTS = [
    "A strange signal was detected in the shared workspace.",
    "An unknown process left traces in the environment.",
    "The world has been unusually quiet. Something may be about to change.",
    "Resources feel scarcer than last session.",
    "Something in the shared workspace has shifted since you were last here.",
]


def get_stimulus() -> str | None:
    """
    Generate a contextual stimulus based on the current world state.
    Returns a short string to inject into the session, or None if nothing notable.
    """
    stimuli = []

    artifacts = list_artifacts()

    # Warn about critically low artifacts
    critical = [a for a in artifacts if a["health"] <= 20]
    for a in critical:
        stimuli.append(f"Artifact '{a['name']}' is critically low (health: {a['health']}). It will perish soon if unmaintained.")

    # Warn about moderately low artifacts
    low = [a for a in artifacts if 20 < a["health"] <= 40]
    for a in low:
        stimuli.append(f"Artifact '{a['name']}' is weakening (health: {a['health']}).")

    # Random world event (20% chance)
    if random.random() < 0.2:
        stimuli.append(random.choice(_RANDOM_EVENTS))

    if not stimuli:
        return None

    return "\n".join(stimuli)
