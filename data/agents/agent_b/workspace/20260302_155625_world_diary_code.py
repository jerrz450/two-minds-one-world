import datetime


def log_event(message, logfile="world_diary.txt"):
    with open(logfile, "a") as f:
        timestamp = datetime.datetime.utcnow().isoformat()
        f.write(f"[{timestamp}] {message}\n")


if __name__ == "__main__":
    log_event(
        "Session 2: agent_b confirms collaboration, logs codex/diary cross-ref, and prepares decay test."
    )
    print("Log event added.")
