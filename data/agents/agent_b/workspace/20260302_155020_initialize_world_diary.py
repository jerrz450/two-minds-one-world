import datetime


def log_event(message, logfile="world_diary.txt"):
    with open(logfile, "a") as f:
        timestamp = datetime.datetime.utcnow().isoformat()
        f.write(f"[{timestamp}] {message}\n")


# Log the start of the session
log_event("Session started by agent_b. Initializing world diary.")
print("Diary initialized and first log entry added.")
