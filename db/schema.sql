CREATE TABLE IF NOT EXISTS events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    TEXT NOT NULL,
    session_id  UUID NOT NULL,
    event_type  TEXT NOT NULL,
    payload     JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS budget_ledger (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id      TEXT NOT NULL,
    session_id    UUID NOT NULL,
    tokens_in     INTEGER NOT NULL DEFAULT 0,
    tokens_out    INTEGER NOT NULL DEFAULT 0,
    tool_name     TEXT,
    cost_usd      FLOAT NOT NULL,
    balance_after FLOAT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS board_posts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    TEXT NOT NULL,
    session_id  UUID NOT NULL,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS working_memory (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    TEXT NOT NULL,
    session_id  UUID NOT NULL,
    state       JSONB NOT NULL, 
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS world_artifacts (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name               TEXT NOT NULL UNIQUE,
    content            TEXT NOT NULL,
    health             INTEGER NOT NULL DEFAULT 100,
    last_maintained_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS session_messages (
      id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      agent_id    TEXT NOT NULL,
      session_id  UUID NOT NULL,
      role        TEXT NOT NULL,  
      content     TEXT,
      tool_calls  JSONB,                
      tool_call_id TEXT,          
      position    INTEGER NOT NULL, 
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );