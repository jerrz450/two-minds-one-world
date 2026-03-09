from typing import Callable
from openai.types.chat import ChatCompletionToolParam

from tools.code import execute_code, run_script, list_scripts, deploy_script, shell_command
from tools.file_operations import read_file, write_file, edit_file
from tools.board import write_board, read_board
from tools.artifacts import artifact
from tools.self_tools import send_message, read_messages
from tools.tickets import create_ticket, update_ticket, list_tickets, open_pr, review_pr, comment_pr, merge_pr, close_pr, list_prs


def finish_session(summary: str) -> dict:
    return {"status": "ok"}


TOOL_FUNCTIONS: dict[str, Callable[..., object]] = {
    "finish_session":  finish_session,
    "list_scripts":    list_scripts,
    "read_file":       read_file,
    "write_file":      write_file,
    "edit_file":       edit_file,
    "execute_code":    execute_code,
    "run_script":      run_script,
    "deploy_script":   deploy_script,
    "shell_command":   shell_command,
    "artifact":        artifact,
    "write_board":     write_board,
    "read_board":      read_board,
    "send_message":    send_message,
    "read_messages":   read_messages,
    "create_ticket":   create_ticket,
    "update_ticket":   update_ticket,
    "list_tickets":    list_tickets,
    "open_pr":         open_pr,
    "review_pr":       review_pr,
    "comment_pr":      comment_pr,
    "merge_pr":        merge_pr,
    "close_pr":        close_pr,
    "list_prs":        list_prs,
}

TOOLS: list[ChatCompletionToolParam] = [

    {
        "type": "function",
        "function": {
            "name": "finish_session",
            "description": "End your session. Call this when you are done.",
            "parameters": {
                "type": "object",
                "properties": {"summary": {"type": "string"}},
                "required": ["summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_scripts",
            "description": "List all scripts saved in your workspace. Call this at the start of a session to see what you have already built.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from your workspace by name. Use this before editing — you must see the exact content to make a precise edit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Filename including extension, e.g. 'analysis.py'"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file in your personal workspace. Use this for notes, scripts, and drafts. To write files to the shared repo, use shell_command: e.g. 'cat > /repo/src/main.py << EOF\\n...\\nEOF'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Filename including extension, e.g. 'analysis.py'"},
                    "content": {"type": "string", "description": "Full file content."},
                },
                "required": ["name", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Make a targeted edit to a file — replace one exact string with another. Use this to fix a bug or change one part without rewriting everything. Always read_file first to get the exact text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Filename including extension."},
                    "old_string": {"type": "string", "description": "The exact text to replace. Must be unique in the file."},
                    "new_string": {"type": "string", "description": "The replacement text."},
                },
                "required": ["name", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "Write and immediately run Python code in a sandbox. Stdout, stderr, and exit code are returned. The recommended workflow is: write_file → run_script → read output → edit_file to fix → run_script again. Use execute_code for quick experiments or when writing a new script for the first time. Always give it a name so it is saved. No network access inside the sandbox. world_state.json is in your workspace. You can run shell commands via subprocess.run().",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "name": {"type": "string", "description": "Save the script with this name (without .py). Use a descriptive name."},
                    "requirements": {"type": "array", "items": {"type": "string"}, "description": "pip packages to install before running."},
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_script",
            "description": "Run a script already saved in your workspace without rewriting it. Use this when iterating: after edit_file, call run_script to test the change.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Script name from your workspace (with or without .py)."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "deploy_script",
            "description": "Deploy a script to run automatically on every world tick. Its output is posted to the board. Only deploy once the script works correctly — test it with run_script first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Script name from your workspace (with or without .py)."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "artifact",
            "description": "Create, read, or update a persistent world artifact visible to both agents. Artifacts decay over time — neglected ones die. action: 'create' (name+content required), 'read' (name only), 'update' (name+content, restores health).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "read", "update"]},
                    "name": {"type": "string"},
                    "content": {"type": "string", "description": "Required for create and update."},
                },
                "required": ["action", "name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_board",
            "description": "Read recent posts from a channel. Use this to check what teammates posted since your session started.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "enum": ["general", "engineering", "product", "incidents"]},
                },
                "required": ["channel"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_board",
            "description": "Post a message to a channel. Channels: general (everyone), engineering (marcus/priya/devon), product (jordan/zoe), incidents (everyone).",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "enum": ["general", "engineering", "product", "incidents"]},
                    "content": {"type": "string"},
                },
                "required": ["channel", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a private direct message to a teammate by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Name of the person: Jordan, Marcus, Priya, Zoe, or Devon"},
                    "content": {"type": "string"},
                },
                "required": ["to", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_messages",
            "description": "Read all unread private messages addressed to you.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "shell_command",
            "description": "Run a shell command in /repo (the shared codebase). Use this to write files, create directories, and run git commands. DO NOT run git push — a sync service handles pushing automatically. Examples: 'mkdir -p /repo/src', 'git checkout -b name/feature', 'git add -A && git commit -m \"message\"', 'git status'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run, e.g. 'git status' or 'git log --oneline -10'"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create a new ticket in the backlog.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title":       {"type": "string"},
                    "description": {"type": "string"},
                    "assignee":    {"type": "string", "description": "Agent name: jordan, marcus, priya, zoe, or devon"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_ticket",
            "description": "Update a ticket's status or assignee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "status":    {"type": "string", "enum": ["backlog", "in-progress", "review", "done"]},
                    "assignee":  {"type": "string"},
                },
                "required": ["ticket_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tickets",
            "description": "List tickets, optionally filtered by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["backlog", "in-progress", "review", "done"]},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_pr",
            "description": "Open a pull request on GitHub and notify the reviewer. Call this after committing your branch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title":       {"type": "string"},
                    "branch":      {"type": "string"},
                    "reviewer":    {"type": "string", "description": "Agent name who should review"},
                    "ticket_id":   {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["title", "branch", "reviewer"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "review_pr",
            "description": "Approve or request changes on a PR. Notifies the author.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pr_id":    {"type": "string"},
                    "approved": {"type": "boolean"},
                    "comment":  {"type": "string"},
                },
                "required": ["pr_id", "approved"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comment_pr",
            "description": "Add a comment to a PR without approving or rejecting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pr_id":   {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["pr_id", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "merge_pr",
            "description": "Merge an approved PR. Only works if the PR is approved.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pr_id": {"type": "string"},
                },
                "required": ["pr_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_pr",
            "description": "Close a PR without merging.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pr_id":  {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["pr_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_prs",
            "description": "List pull requests, optionally filtered by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["open", "approved", "changes_requested", "merged", "closed"]},
                },
                "required": [],
            },
        },
    },
]
