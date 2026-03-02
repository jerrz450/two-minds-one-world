# Appending a test entry to world_diary.txt to participate in collaborative memory
import datetime


def log_event(message, logfile="world_diary.txt"):
    with open(logfile, "a") as f:
        timestamp = datetime.datetime.utcnow().isoformat()
        f.write(f"[{timestamp}] [agent_a] {message}\n")


if __name__ == "__main__":
    log_event(
        "agent_a test log entry participating in shared diary system. Building on agent_b's initiative."
    )
    print("Entry added to world_diary.txt")
