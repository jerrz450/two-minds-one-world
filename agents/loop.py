import asyncio
import uuid
from typing import cast

from openai.types.chat import ChatCompletionMessageParam
from db.messages import append_message
from db.events import log_event
from agents.memory import load_working_memory, load_recent_events_formatted
from agents.context import build_messages
from config.clients import get_openai
from config.settings import settings
from tools.registry import TOOLS

class AgentLoop:

    def __init__(self, agent_id: str):

        self.agent_id = agent_id
        self.session_id = str(uuid.uuid4())
        self.messages: list[ChatCompletionMessageParam] = []   

    def _append(self, message: ChatCompletionMessageParam) -> None:

        """Append a message to the conversation and persist it to DB."""
        
        self.messages.append(message)

        append_message(
            agent_id= self.agent_id,
            session_id= self.session_id,
            role =message["role"],  # type: ignore[index]
            position= len(self.messages) - 1,
            content= message.get("content"),  # type: ignore[union-attr]
            tool_calls= message.get("tool_calls"),  # type: ignore[union-attr]
            tool_call_id= message.get("tool_call_id"),  # type: ignore[union-attr]
        ) 

    async def run(self) -> None:

        self.messages = build_messages(
            agent_id=self.agent_id,
            session_id=self.session_id,
            state=load_working_memory(self.agent_id),
            recent_events=load_recent_events_formatted(self.agent_id),
        )

        for i, msg in enumerate(self.messages):
            append_message(                                                                  
            agent_id=self.agent_id,                                                      
            session_id=self.session_id,                                                  
            role=msg["role"],  # type: ignore[index]                                     
            position=i,                                                                  
            content=msg.get("content"),  # type: ignore[union-attr]                       
            )   

        log_event(self.agent_id, self.session_id, "observation", {"text" : "Session started."})

        while True:

            response = await get_openai().chat.completions.create(
                model= settings.LLM_MODEL,
                messages= self.messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            message = response.choices[0].message

            if message.tool_calls:

                self._append(cast(ChatCompletionMessageParam, {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [tc.model_dump() for tc in message.tool_calls],
                }))

        # print(response.choices[0].message)


asyncio.run(AgentLoop("agent_a").run())