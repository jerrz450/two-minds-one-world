from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class Event(BaseModel):
    id: UUID
    agent_id: str
    session_id: UUID
    event_type: str  # thought | tool_call | tool_result | memory_write | observation
    payload: dict
    created_at: datetime


class BudgetEntry(BaseModel):
    id: UUID
    agent_id: str
    session_id: UUID
    tokens_in: int
    tokens_out: int
    tool_name: str | None  # None = LLM call
    cost_usd: float
    balance_after: float
    created_at: datetime


class BoardPost(BaseModel):
    id: UUID
    agent_id: str
    session_id: UUID
    content: str
    created_at: datetime


class WorkingMemoryState(BaseModel):

    """The structured content inside working_memory.state JSONB column."""

    beliefs_world: str
    beliefs_self: str
    beliefs_other_agent: str | None
    active_goals: list[str]
    open_questions: list[str]
    budget_status: str
    relationship_state: str | None


class WorkingMemory(BaseModel):
    id: UUID
    agent_id: str
    session_id: UUID
    state: WorkingMemoryState
    created_at: datetime


class SessionMessage(BaseModel):
    id: UUID
    agent_id: str
    session_id: UUID
    role: str           # system | user | assistant | tool
    content: str | None
    tool_calls: list | None
    tool_call_id: str | None
    position: int
    created_at: datetime


class WorldArtifact(BaseModel):
    id: UUID
    name: str
    content: str
    health: int
    last_maintained_at: datetime
    created_at: datetime
