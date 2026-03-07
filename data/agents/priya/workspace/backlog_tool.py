#!/usr/bin/env python3
import argparse
import os

LOG_FILE = "backlog.txt"

def add_ticket(priority, description):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{priority}] {description}\n")
        print(f"Ticket added: [{priority}] {description}")


def list_tickets():
    if not os.path.exists(LOG_FILE):
        print("Backlog is empty")
        return

    with open(LOG_FILE, "r") as f:
        print("\nPending Tickets:")
        for line in sorted(f, key=lambda x: int(x.split("[\"]1").strip()) if x.strip() else 9999):
            print(line.strip())


def main():
    parser = argparse.ArgumentParser(description='Backlog manager')
    parser.add_argument('command', choices=['add', 'list'])
    parser.add_argument('--priority', type=int, help='Ticket priority')
    parser.add_argument('--description', help='Ticket description')

    args = parser.parse_args()

    if args.command == 'add' and args.priority and args.description:
        add_ticket(args.priority, args.description)
    elif args.command == 'list':
        list_tickets()
    else:
        print("Invalid command or missing parameters")

if __name__ == '__main__':
    main()