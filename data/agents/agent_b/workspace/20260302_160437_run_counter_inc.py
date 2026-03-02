# Run the persistent counter with action 'inc' to create and increment the counter.
import sys
from subprocess import run, PIPE

script_name = "20260302_160430_persistent_counter.py"
result = run([sys.executable, script_name, "inc"], stdout=PIPE, stderr=PIPE)
print(result.stdout.decode())
if result.stderr:
    print("STDERR:", result.stderr.decode())
