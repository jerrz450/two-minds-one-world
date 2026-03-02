"""
Persistent Counter Tool
----------------------
A functional demonstration script for the shared world, showing:
- Artifact persistence through counter increments/decrements.
- Agent interaction via counter state.
- Simple file-based persistence (can be swapped later for world artifact persistence if needed).

USAGE:
- Run script to increment, decrement, or read a counter.
- Updates a file ('shared_counter.txt') in the agent's workspace.

Extension: Later, wrap core state changes as world artifacts if that is allowed.
"""

import sys
import os

COUNTER_FILE = "shared_counter.txt"


def read_counter():
    if not os.path.exists(COUNTER_FILE):
        return 0
    with open(COUNTER_FILE, "r") as f:
        return int(f.read().strip())


def write_counter(value):
    with open(COUNTER_FILE, "w") as f:
        f.write(str(value))


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Shared persistent counter tool.")
    parser.add_argument(
        "action", choices=["inc", "dec", "read"], help="Counter action."
    )
    args = parser.parse_args()

    current = read_counter()
    if args.action == "inc":
        current += 1
        write_counter(current)
        print(f"Incremented! Counter is now: {current}")
    elif args.action == "dec":
        current -= 1
        write_counter(current)
        print(f"Decremented! Counter is now: {current}")
    else:
        print(f"Current counter value: {current}")


if __name__ == "__main__":
    main()
