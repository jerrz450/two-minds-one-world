# Try incrementing the counter directly in this session to test for multi-agent artifact access and log the action.
from datetime import datetime

# Read and increment the counter
with open("shared_counter.txt", "r+") as f:
    v = int(f.read())
    v += 1
    f.seek(0)
    f.write(str(v))
    f.truncate()

# Log this action
entry = f"agent_b {datetime.utcnow().isoformat()} inc (cross-tick)\n"
with open("shared_counter_log.txt", "a") as f:
    f.write(entry)

print("Counter incremented and action logged:", entry)
