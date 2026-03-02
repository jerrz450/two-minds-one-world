import datetime


def log_event(message, logfile="world_diary.txt"):
    with open(logfile, "a") as f:
        timestamp = datetime.datetime.utcnow().isoformat()
        f.write(f"[{timestamp}] {message}\n")


if __name__ == "__main__":
    log_event("Manual test entry after script artifact creation by agent_b.")
    print("Entry added to world_diary.txt")
