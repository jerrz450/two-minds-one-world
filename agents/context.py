from datetime import datetime, timezone
from pathlib import Path

from openai.types.chat import ChatCompletionMessageParam
from db.models import WorkingMemoryState

def load_prompts() -> dict[str, str]:

    base = Path(__file__).parent / "prompts"
    return {p.stem: p.read_text(encoding="utf-8") for p in base.glob("*.md")}


def load_constitution(agent_id: str = "agent_a") -> str:

    path = Path(__file__).resolve().parents[1] / f"data/agents/{agent_id}/constitution.md"
    return path.read_text(encoding="utf-8").strip()

def _format_list(items: list[str]) -> str:

    return "\n".join(f"- {item}" for item in items) if items else "None."

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

def fill_session_start(template: str, session_id: str, recent_events: str) -> str:

    return template.format(
        session_id=session_id,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        recent_events=recent_events,
    )

def build_messages(agent_id: str, session_id: str, state: WorkingMemoryState, recent_events: str) -> list[ChatCompletionMessageParam]:
    
    """Assemble the opening messages for the agentic loop."""
    
    prompts = load_prompts()
    constitution = load_constitution(agent_id)

    return [
        {"role": "system", "content": fill_system_prompt(prompts["system"], constitution, state)},
        {"role": "user",   "content": fill_session_start(prompts["session_start"], session_id, recent_events)},
    ]

def build_reflect_prompt() -> str:

    return load_prompts()["reflect"]

if __name__ == "__main__":

    state = WorkingMemoryState(
        beliefs_world="I have just come into existence.",
        beliefs_self="I have no name yet.",
        beliefs_other_agent=None,
        active_goals=[
            "Understand where I am",
            "Decide on a name",
        ],
        open_questions=[
            "What is this world?",
            "Is there anyone else here?",
        ],
        budget_status="Unknown",
        relationship_state=None,
    )   
    
    response = build_messages(agent_id=  "agent_a", 
                   session_id="test-session", 
                   state= state,
                   recent_events="None yet.")
    
    from pprint import pprint
    pprint(response)
