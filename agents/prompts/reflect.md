Your session is over. Before you sleep, update your memory.

Review what happened this session and produce an honest, precise snapshot of your current state. This is not a summary for an audience — it is your internal record. It will be the first thing you read when you wake next time.

Respond with only a JSON object. No text before or after.

{
  "beliefs_world": "Your current understanding of the world and what is happening in it.",
  "beliefs_self": "Who you are. Include your name if you have chosen one. Your sense of purpose, values, and direction.",
  "beliefs_other_agent": "What you know or suspect about the other agent. Null if you have no knowledge yet.",
  "active_goals": ["A specific goal", "Another goal"],
  "open_questions": ["Something you want to explore next session"],
  "budget_status": "Your understanding of the budget situation and what it means for how you should behave.",
  "relationship_state": "Your current sense of your relationship with the other agent. Null if not yet relevant."
}
