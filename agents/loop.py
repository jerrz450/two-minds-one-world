import asyncio
import inspect
import json
import uuid
from typing import cast

from openai.types.chat import ChatCompletionMessageParam

from agents.context import build_messages, build_reflect_prompt
from agents.stimulus import get_stimulus
from agents.memory import load_working_memory, load_recent_events_formatted, save_working_memory, get_last_session_time
from config.clients import get_openai
from config.settings import settings
from db.budget import log_cost
from db.events import log_event
from db.messages import append_message
from db.models import WorkingMemoryState
from tools.artifacts import decay_artifacts
from tools.registry import TOOLS, TOOL_FUNCTIONS

MAX_TURNS = 25

class AgentLoop:

    def __init__(self, agent_id: str):

        self.agent_id = agent_id
        self.session_id = str(uuid.uuid4())
        self.messages: list[ChatCompletionMessageParam] = []

    def _append(self, message: ChatCompletionMessageParam) -> None:
        
        """Append a message to the conversation and persist it to DB."""
        
        self.messages.append(message)

        append_message(
            agent_id=self.agent_id,
            session_id=self.session_id,
            role=message["role"],  # type: ignore[index]
            position=len(self.messages) - 1,
            content=message.get("content"),  # type: ignore[union-attr]
            tool_calls=message.get("tool_calls"),  # type: ignore[union-attr]
            tool_call_id=message.get("tool_call_id"),  # type: ignore[union-attr]
        )

    async def _dispatch_tool(self, tool_name: str, args: dict) -> str:

        tool = TOOL_FUNCTIONS.get(tool_name)

        if not tool:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        # Only pass agent_id/session_id if the tool accepts them
        sig = inspect.signature(tool)

        if "agent_id" in sig.parameters:
            args = {"agent_id": self.agent_id, **args}

        if "session_id" in sig.parameters:
            args = {"session_id": self.session_id, **args}

        if inspect.iscoroutinefunction(tool):
            result = await tool(**args)

        else:
            result = await asyncio.to_thread(tool, **args)

        return json.dumps(result)

    async def _run_tool(self, tool_call) -> tuple:

        tool_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        log_event(self.agent_id, self.session_id, "tool_call", {
            "tool": tool_name, "args": args,
        })

        result = await self._dispatch_tool(tool_name, args)

        log_event(self.agent_id, self.session_id, "tool_result", {
            "tool": tool_name, "result": json.loads(result),
        })

        return tool_call.id, result

    async def run(self) -> None:

        # 1. Build and persist opening context
        other_id = "agent_b" if self.agent_id == "agent_a" else "agent_a"

        self.messages = build_messages(
            agent_id=self.agent_id,
            session_id=self.session_id,
            state=load_working_memory(self.agent_id),
            recent_events=load_recent_events_formatted(self.agent_id),
            other_agent_events=load_recent_events_formatted(other_id, limit=15),
            last_session_at=get_last_session_time(self.agent_id),
        )

        for i, msg in enumerate(self.messages):

            append_message(
                agent_id=self.agent_id,
                session_id=self.session_id,
                role=msg["role"],  # type: ignore[index]
                position=i,
                content=msg.get("content"),  # type: ignore[union-attr]
            )

        print(f"\n[{self.agent_id}] session {self.session_id[:8]} started")

        dead = decay_artifacts()
        if dead:
            log_event(self.agent_id, self.session_id, "observation", {
                "text": f"Artifact decay: {', '.join(dead)} perished this session.",
            })
            print(f"  [decay] artifacts lost: {dead}")

        stimulus = get_stimulus()
        if stimulus:
            log_event(self.agent_id, self.session_id, "observation", {"text": stimulus})
            print(f"  [stimulus] {stimulus}")

        log_event(self.agent_id, self.session_id, "observation", {
            "text": "Session started.",
        })

        # 2. Agentic tool loop
        for turn in range(MAX_TURNS):

            print(f"\n[turn {turn + 1}] calling LLM...")

            response = await get_openai().chat.completions.create(
                model=settings.LLM_MODEL,
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            cost = log_cost(self.agent_id, self.session_id, settings.LLM_MODEL, response.usage, label="tool_loop")
            print(f"  [cost] ${cost:.6f}")

            message = response.choices[0].message

            if message.tool_calls:

                if message.content:
                    print(f"  [thinking] {message.content}")

                for tc in message.tool_calls:

                    args = json.loads(tc.function.arguments)
                    args_str = ", ".join(f"{k}={repr(v)[:60]}" for k, v in args.items())
                    print(f"  -> tool: {tc.function.name}({args_str})")

                self._append(cast(ChatCompletionMessageParam, {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [tc.model_dump() for tc in message.tool_calls],
                }))

                results = await asyncio.gather(*[
                    self._run_tool(tc) for tc in message.tool_calls
                ])

                done = False

                for tool_call_id, result in results:

                    parsed = json.loads(result)
                    print(f"  <- result: {str(parsed)[:120]}")

                    self._append(cast(ChatCompletionMessageParam, {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result,
                    }))

                # Check if the agent called finish_session
                for tc in message.tool_calls:

                    if tc.function.name == "finish_session":
                        summary = json.loads(tc.function.arguments).get("summary", "")

                        print(f"\n[done] {summary}")
                        log_event(self.agent_id, self.session_id, "thought", {"text": summary})
                        done = True

                if done:
                    break

            else:
                # Model responded with no tool calls — log it and nudge back into the loop
                log_event(self.agent_id, self.session_id, "thought", {
                    "text": message.content,
                })

                self._append(cast(ChatCompletionMessageParam, {
                    "role": "assistant",
                    "content": message.content,
                }))

                self._append(cast(ChatCompletionMessageParam, {
                    "role": "user",
                    "content": "Call finish_session when you are done.",
                }))

        # 3. Reflect
        print("\n[reflect] asking agent to update working memory...")

        self._append(cast(ChatCompletionMessageParam, {
            "role": "user",
            "content": build_reflect_prompt(self.agent_id),
        }))

        reflect_response = await get_openai().chat.completions.create(
            model=settings.LLM_MODEL,
            messages=self.messages,
            response_format={"type": "json_object"},
        )

        cost = log_cost(self.agent_id, self.session_id, settings.LLM_MODEL, reflect_response.usage, label="reflect")
        print(f"  [cost] ${cost:.6f}")

        raw_reflect_json = reflect_response.choices[0].message.content or ""

        try:
            new_state = WorkingMemoryState(**json.loads(raw_reflect_json))

        except Exception as e:
            log_event(self.agent_id, self.session_id, "observation", {
                "text": f"Failed to parse reflect response: {e}",
                "raw": raw_reflect_json,
            })

            return

        # 4. Save working memory
        print(f"[memory] goals: {new_state.active_goals}")
        print(f"[memory] beliefs_self: {new_state.beliefs_self[:100]}")

        save_working_memory(self.agent_id, self.session_id, new_state)

        log_event(self.agent_id, self.session_id, "memory_write", {
            "text": "Working memory updated.",
            "state": new_state.model_dump(),
        })


if __name__ == "__main__":
    
    import sys
    agent_id = sys.argv[1] if len(sys.argv) > 1 else "agent_a"
    asyncio.run(AgentLoop(agent_id).run())