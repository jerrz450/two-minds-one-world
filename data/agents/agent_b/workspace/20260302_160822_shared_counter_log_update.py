# Add a usage log to the shared_counter.txt artifact by writing to a new file, tracking actions.
# Each agent and timestamped action is appended to shared_counter_log.txt for future analysis.
from datetime import datetime

log_entry = f"agent_b {datetime.utcnow().isoformat()} inc\n"
with open("shared_counter_log.txt", "a") as f:
    f.write(log_entry)

print("Logged action to shared_counter_log.txt:", log_entry)
