from typing import Callable
from openai.types.chat import ChatCompletionToolParam

from tools.code import execute_code, run_script, list_scripts, deploy_script
from tools.file_operations import read_file, write_file, edit_file
from tools.board import write_board
from tools.artifacts import artifact
from tools.self_tools import send_message, read_messages


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
    "artifact":        artifact,
    "write_board":     write_board,
    "send_message":    send_message,
    "read_messages":   read_messages,
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
            "description": "Create or overwrite a file in your workspace. Use this to write a new script or fully replace an existing one.",
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
            "name": "write_board",
            "description": "Post a message to the public board. Visible to all agents and human observers.",
            "parameters": {
                "type": "object",
                "properties": {"content": {"type": "string"}},
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a private message to the other agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                },
                "required": ["content"],
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
]
