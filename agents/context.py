import re
from datetime import datetime, timezone
from pathlib import Path

from openai.types.chat import ChatCompletionMessageParam
from db.models import WorkingMemoryState
from tools.board import read_board
from tools.artifacts import list_artifacts
from tools.code import list_scripts
from tools.tickets import list_prs
from world.world_main import get_recent_world_events
from db.events import get_last_session_tool_counts

_ROOT = Path(__file__).resolve().parents[1]

def load_prompts(agent_id: str = "agent_a") -> dict[str, str]:
    
    """
    Load prompt templates. Agent-specific overrides in
    data/agents/{agent_id}/prompts/ take precedence over shared agents/prompts/.
    """

    shared  = Path(__file__).parent / "prompts"
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
        i_am=state.i_am,
        i_believe=state.i_believe,
        i_want=_format_list(state.i_want),
        i_suspect=state.i_suspect or "",
        i_fear=state.i_fear or "",
        unresolved=_format_list(state.unresolved),
        budget_feel=state.budget_feel,
    )


def _format_board(posts: list[dict]) -> str:

    if not posts:
        return "No posts yet."
    
    by_channel: dict[str, list[str]] = {}

    for p in posts[-20:]:
        by_channel.setdefault(p.get("channel", "general"), []).append(p["content"])

    lines = []

    for ch, contents in by_channel.items():
        lines.append(f"#{ch}")
        lines.extend(f"  {c}" for c in contents)

    return "\n".join(lines)


def _format_prs(agent_id: str) -> str:
    
    prs = [p for p in list_prs(agent_id, "") if p["status"] not in ("merged", "closed") and (p["author"] == agent_id or p["reviewer"] == agent_id)]
    
    if not prs:
        return "None."
    
    lines = []

    for p in prs:
        role = "author" if p["author"] == agent_id else "reviewer"
        lines.append(f"- [{p['id']}] {p['title']} ({p['status']}, you are {role})")

    return "\n".join(lines)


def _format_artifacts(artifacts: list[dict]) -> str:
    
    if not artifacts:
        return "None."
    
    return "\n".join(f"- {a['name']}" for a in artifacts)


def fill_session_start(
    template: str,
    session_id: str,
    recent_events: str,
    last_session_at: datetime | None,
    board: str,
    artifacts: str,
    prs: str,
    i_want: list[str],
    world_events: str,
    tool_usage: str,
    workspace: str,
    workspace_contents: str,
    todo: str,
    identity: str,
) -> str:

    return template.format(
        session_id=session_id,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        recent_events=recent_events,
        session_gap=_format_gap(last_session_at),
        board=board,
        artifacts=artifacts,
        prs=prs,
        i_want=_format_list(i_want),
        world_events=world_events,
        tool_usage=tool_usage,
        workspace=workspace,
        workspace_contents=workspace_contents,
        todo=todo,
        identity=identity,
    )


def build_messages(
    agent_id: str,
    session_id: str,
    state: WorkingMemoryState,
    recent_events: str,
    last_session_at: datetime | None = None,
) -> list[ChatCompletionMessageParam]:

    """Assemble the opening messages for the agentic loop."""

    prompts = load_prompts(agent_id)
    constitution = load_constitution(agent_id)

    from tools.board import CHANNELS

    all_posts = []

    for ch in CHANNELS:
        all_posts.extend(read_board(agent_id=agent_id, channel=ch))

    board = _format_board(all_posts)
    artifacts = _format_artifacts(list_artifacts())
    prs = _format_prs(agent_id)
    world_events = "\n".join(get_recent_world_events()) or "No world events yet."

    counts = get_last_session_tool_counts(agent_id)

    if counts:
        tool_usage = "Tool usage last session: " + ", ".join(f"{t}×{n}" for t, n in counts.items())
    else:
        tool_usage = ""

    workspace = f"/app/data/agents/{agent_id}/workspace"
    scripts = list_scripts(agent_id, "")
    workspace_contents = ", ".join(scripts.get("scripts", [])) or "empty"

    ws_path = Path("/app/data/agents") / agent_id / "workspace"
    todo = (ws_path / "TODO.md").read_text(encoding="utf-8").strip() if (ws_path / "TODO.md").exists() else "No todos yet. Create TODO.md to track your objectives."
    identity = (ws_path / "IDENTITY.md").read_text(encoding="utf-8").strip() if (ws_path / "IDENTITY.md").exists() else "You have not yet defined yourself. Create IDENTITY.md to establish who you are."

    return [
        {"role": "system", "content": fill_system_prompt(prompts["system"], constitution, state)},
        {"role": "user",   "content": fill_session_start(
            prompts["session_start"], session_id, recent_events,
            last_session_at, board, artifacts, prs,
            state.i_want, world_events, tool_usage, workspace, workspace_contents, todo, identity,
        )},
    ]

def build_reflect_prompt(agent_id: str = "agent_a") -> str:

    return load_prompts(agent_id)["reflect"]
