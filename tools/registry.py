# OpenAI tool schemas — passed to every API call so the model knows what tools exist.
# The name here must exactly match the function name dispatched in loop.py.

from openai.types.chat import ChatCompletionToolParam

TOOLS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "write_journal",
            "description": "Write an entry to your private journal. Only you can read this. Use it to think out loud, record a decision, or capture something worth remembering.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The journal entry to write.",
                    }
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_board",
            "description": "Post a message to the public bulletin board. Anyone can read it — including the other agent and human observers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The message to post on the bulletin board.",
                    }
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_board",
            "description": "Read all current posts on the public bulletin board.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_budget_status",
            "description": "Check the current shared budget. Shows remaining balance, burn rate, and estimated sessions left. Always free to call.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]
