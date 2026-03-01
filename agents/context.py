from datetime import datetime, timezone
from pathlib import Path

from openai.types.chat import ChatCompletionMessageParam
from db.models import WorkingMemoryState
from tools.board import read_board
from tools.artifacts import list_artifacts

_ROOT = Path(__file__).resolve().parents[1]


def load_prompts(agent_id: str = "agent_a") -> dict[str, str]:
    """
    Load prompt templates. Agent-specific overrides in
    data/agents/{agent_id}/prompts/ take precedence over shared agents/prompts/.
    """
    shared   = Path(__file__).parent / "prompts"
    override = _ROOT / f"data/agents/{agent_id}/prompts"

    prompts = {p.stem: p.read_text(encoding="utf-8") for p in shared.glob("*.md")}

    if override.exists():
        for p in override.glob("*.md"):
            prompts[p.stem] = p.read_text(encoding="utf-8")

    return prompts


def load_constitution(agent_id: str = "agent_a") -> str:
    # Check for agent-specific override first
    override = _ROOT / f"data/agents/{agent_id}/prompts/constitution.md"
    default  = _ROOT / f"data/agents/{agent_id}/constitution.md"
    path = override if override.exists() else default
    return path.read_text(encoding="utf-8").strip()


def _format_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "None."


def _format_gap(last_session_at: datetime | None) -> str:
    if last_session_at is None:
        return "This is your first session."
    delta = datetime.now(timezone.utc) - last_session_at
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes = remainder // 60
    if hours > 0:
        return f"{hours}h {minutes}m since your last session."
    return f"{minutes}m since your last session."


def fill_system_prompt(template: str, constitution: str, state: WorkingMemoryState) -> str:
    return template.format(
        constitution=constitution,
        beliefs_world=state.beliefs_world,
        beliefs_self=state.beliefs_self,
        beliefs_other_agent=state.beliefs_other_agent or "Not yet encountered.",
        active_goals=_format_list(state.active_goals),
        open_questions=_format_list(state.open_questions),
        budget_status=state.budget_status,
        relationship_state=state.relationship_state or "Not yet relevant.",
    )


def _format_board(posts: list[dict]) -> str:
    if not posts:
        return "No posts yet."
    return "\n".join(f"[{p['agent_id']}] {p['content']}" for p in posts[-10:])


def _format_artifacts(artifacts: list[dict]) -> str:
    if not artifacts:
        return "None."
    return "\n".join(f"- {a['name']} (health: {a['health']})" for a in artifacts)


def fill_session_start(
    template: str,
    session_id: str,
    recent_events: str,
    last_session_at: datetime | None,
    other_agent_events: str,
    board: str,
    artifacts: str,
    active_goals: list[str],
) -> str:
    return template.format(
        session_id=session_id,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        recent_events=recent_events,
        session_gap=_format_gap(last_session_at),
        other_agent_events=other_agent_events,
        board=board,
        artifacts=artifacts,
        active_goals=_format_list(active_goals),
    )


def build_messages(
    agent_id: str,
    session_id: str,
    state: WorkingMemoryState,
    recent_events: str,
    other_agent_events: str,
    last_session_at: datetime | None = None,
) -> list[ChatCompletionMessageParam]:
    """Assemble the opening messages for the agentic loop."""
    prompts      = load_prompts(agent_id)
    constitution = load_constitution(agent_id)

    board     = _format_board(read_board())
    artifacts = _format_artifacts(list_artifacts())

    return [
        {"role": "system", "content": fill_system_prompt(prompts["system"], constitution, state)},
        {"role": "user",   "content": fill_session_start(
            prompts["session_start"], session_id, recent_events,
            last_session_at, other_agent_events, board, artifacts,
            state.active_goals,
        )},
    ]


def build_reflect_prompt(agent_id: str = "agent_a") -> str:
    return load_prompts(agent_id)["reflect"]