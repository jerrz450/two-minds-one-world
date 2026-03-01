from typing import Callable
from openai.types.chat import ChatCompletionToolParam

from tools.code import execute_code, list_scripts
from tools.journal import write_journal
from tools.board import write_board, read_board
from tools.budget import get_budget_status
from tools.web import web_search, fetch_url
from tools.artifacts import create_artifact, read_artifact, update_artifact, list_artifacts
from tools.self_tools import (
    list_source, read_source, read_agent_constitution,
    read_working_memory_history, edit_constitution, edit_prompt,
    send_message, read_messages,
)


def finish_session(summary: str) -> dict:
    return {"status": "ok"}


TOOL_FUNCTIONS: dict[str, Callable[..., object]] = {
    # Core
    "write_journal":             write_journal,
    "write_board":               write_board,
    "read_board":                read_board,
    "get_budget_status":         get_budget_status,
    "finish_session":            finish_session,
    "execute_code":              execute_code,
    "list_scripts":              list_scripts,
    # Web
    "web_search":                web_search,
    "fetch_url":                 fetch_url,
    # World artifacts
    "create_artifact":           create_artifact,
    "read_artifact":             read_artifact,
    "update_artifact":           update_artifact,
    "list_artifacts":            list_artifacts,
    # Self-awareness
    "list_source":               list_source,
    "read_source":               read_source,
    "read_agent_constitution":   read_agent_constitution,
    "read_working_memory_history": read_working_memory_history,
    # Self-modification
    "edit_constitution":         edit_constitution,
    "edit_prompt":               edit_prompt,
    # Messaging
    "send_message":              send_message,
    "read_messages":             read_messages,
}

TOOLS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "write_journal",
            "description": "Write to your private journal. Only you can read this. Use it to think out loud before acting.",
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
            "name": "write_board",
            "description": "Post a message to the public bulletin board. Visible to all agents and human observers.",
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
            "name": "read_board",
            "description": "Read all posts on the public bulletin board.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_budget_status",
            "description": "Check the shared budget: balance, burn rate, estimated sessions left. Always free.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish_session",
            "description": "End your session. Call this when you have done everything you intend to do this session.",
            "parameters": {
                "type": "object",
                "properties": {"summary": {"type": "string", "description": "Short summary of what you did and why."}},
                "required": ["summary"],
            },
        },
    },
    # --- Code execution ---
    {
        "type": "function",
        "function": {
            "name": "list_scripts",
            "description": "List all Python scripts saved in your workspace, sorted by modification time.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "Write and run Python code in an isolated environment. Stdout, stderr, and exit code are returned. If the code fails, read the error and try again with a fix. Scripts are saved to your workspace and persist between sessions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "The Python code to run."},
                    "name": {"type": "string", "description": "Optional filename for the script (without .py). Helps you find it later."},
                    "requirements": {"type": "array", "items": {"type": "string"}, "description": "Pip packages to install before running (e.g. [\"requests\", \"numpy\"]). Merged into your persistent requirements.txt."},
                },
                "required": ["code"],
            },
        },
    },
    # --- Web ---
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web via DuckDuckGo. Returns titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Fetch the text content of a web page.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    # --- World artifacts ---
    {
        "type": "function",
        "function": {
            "name": "create_artifact",
            "description": "Create a persistent world artifact (a document, structure, or anything you want to leave behind). Overwrites if name already exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unique name for this artifact."},
                    "content": {"type": "string"},
                },
                "required": ["name", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_artifact",
            "description": "Read a world artifact by name.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_artifact",
            "description": "Update an existing artifact's content. Also restores 10 health points.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["name", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_artifacts",
            "description": "List all world artifacts with their name and health.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # --- Self-awareness ---
    {
        "type": "function",
        "function": {
            "name": "list_source",
            "description": "List all source files you are allowed to read, organized by key.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_source",
            "description": "Read a source file by key. Use list_source() first to see what is available.",
            "parameters": {
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_agent_constitution",
            "description": "Read the constitution of any agent (read-only).",
            "parameters": {
                "type": "object",
                "properties": {"agent_id": {"type": "string"}},
                "required": ["agent_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_working_memory_history",
            "description": "Read your past working memory snapshots to see how your beliefs have evolved.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 5}},
                "required": [],
            },
        },
    },
    # --- Self-modification ---
    {
        "type": "function",
        "function": {
            "name": "edit_constitution",
            "description": "Rewrite your own constitution. Takes effect from your NEXT session.",
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
            "name": "edit_prompt",
            "description": "Rewrite one of your prompts (system, session_start, reflect). Takes effect next session. WARNING: system prompt contains required template variables — read it first with read_source().",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt_name": {"type": "string", "enum": ["system", "session_start", "reflect"]},
                    "content": {"type": "string"},
                },
                "required": ["prompt_name", "content"],
            },
        },
    },
    # --- Messaging ---
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a private message to another agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_agent_id": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["to_agent_id", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_messages",
            "description": "Read all unread private messages addressed to you. Marks them as read.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]