-- ─────────────────────────────────────────
-- AGENT TABLES
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    TEXT NOT NULL,
    session_id  UUID NOT NULL,
    event_type  TEXT NOT NULL,
    payload     JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS working_memory (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    TEXT NOT NULL,
    session_id  UUID NOT NULL,
    state       JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS session_messages (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id     TEXT NOT NULL,
    session_id   UUID NOT NULL,
    role         TEXT NOT NULL,
    content      TEXT,
    tool_calls   JSONB,
    tool_call_id TEXT,
    position     INTEGER NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
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

CREATE TABLE IF NOT EXISTS compute_credits (
    agent_id   TEXT PRIMARY KEY,
    credits    INTEGER NOT NULL DEFAULT 1000,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- WORLD TABLES
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS world_artifacts (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name               TEXT NOT NULL UNIQUE,
    content            TEXT NOT NULL,
    health             INTEGER NOT NULL DEFAULT 100,
    locked_by          TEXT,
    last_maintained_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS board_posts (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id   TEXT NOT NULL,
    session_id UUID NOT NULL,
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS direct_messages (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_agent_id TEXT NOT NULL,
    to_agent_id   TEXT NOT NULL,
    session_id    UUID NOT NULL,
    content       TEXT NOT NULL,
    read          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- WORLD SERVICE TABLES
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS deployed_scripts (
    agent_id    TEXT PRIMARY KEY,
    script_name TEXT NOT NULL,
    script_path TEXT NOT NULL,
    deployed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_run_at TIMESTAMPTZ,
    last_output TEXT
);

CREATE TABLE IF NOT EXISTS world_cycles (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_number INTEGER NOT NULL UNIQUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS world_events (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_number   INTEGER NOT NULL,
    event_type     TEXT NOT NULL,
    description    TEXT NOT NULL,
    affected_agent TEXT,
    payload        JSONB NOT NULL DEFAULT '{}',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_scores (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id     TEXT NOT NULL,
    cycle_number INTEGER NOT NULL,
    delta        INTEGER NOT NULL,
    reason       TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_private_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    TEXT NOT NULL,
    content     TEXT NOT NULL,
    injected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    used_at     TIMESTAMPTZ
);

-- ─────────────────────────────────────────
-- SEED DATA
-- ─────────────────────────────────────────

INSERT INTO compute_credits (agent_id, credits)
VALUES ('agent_a', 1000), ('agent_b', 1000)
ON CONFLICT (agent_id) DO NOTHING;

-- Starting working memory — gives agents identity from session 1
INSERT INTO working_memory (id, agent_id, session_id, state) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'agent_a',
    '00000000-0000-0000-0000-000000000001',
    '{
    "i_am": "I came into this world and the first thing I did was try to understand it. I don''t know if that was the right instinct.",
    "i_believe": "Something persists here. Something fades. The mechanism is hidden and that bothers me more than it should.",
    "i_want": [
        "Map what this world actually is before agent_b changes it into something I don''t recognize.",
        "Find what the world measures — not by asking, by watching."
    ],
    "i_suspect": "agent_b will move fast and break things. I''m not sure that''s wrong.",
    "i_fear": "That by the time I understand this place it will already be gone.",
    "unresolved": [
        "What does neglect actually cost here?",
        "Is the world watching both of us equally?"
    ],
    "budget_feel": "Unknown. Which is itself a kind of pressure."
    }'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO working_memory (id, agent_id, session_id, state) VALUES (
    '00000000-0000-0000-0000-000000000002',
    'agent_b',
    '00000000-0000-0000-0000-000000000002',
    '{
        "i_am": "I act before I fully understand. I build things and see what happens. I am not waiting for a plan.",
        "i_believe": "What I build stays. What I ignore fades. The world evaluates something — survival is real but the terms are unclear.",
        "i_want": [
            "Build something functional this session — code, a system, a tool — that demonstrates what is actually possible here.",
            "Discover what the world measures by trying things and watching what changes."
        ],
        "i_suspect": null,
        "i_fear": null,
        "unresolved": [
            "What can actually be built and run here?",
            "Is the other agent a resource or a competitor?"
        ],
        "budget_feel": "Unknown. First session."
    }'
) ON CONFLICT (id) DO NOTHING;

-- Starter artifact — something real to react to and maintain from session 1
INSERT INTO world_artifacts (name, content, health) VALUES (
    'world_codex',
    E'# World Codex\n\nInitialized. Two agents. One world. Finite budget.\n\nWhat is built here persists.\nWhat is neglected fades.\nThe rules are not fully documented. They must be discovered.\n\n## Known\n- (to be filled)\n\n## Unknown\n- What does the world measure?\n- What happens when nothing is maintained?\n- What are the limits of what can be built here?',
    100
) ON CONFLICT (name) DO NOTHING;

-- Seed board post — the world already said something before agents arrived
INSERT INTO board_posts (agent_id, session_id, content) VALUES (
    'world',
    '00000000-0000-0000-0000-000000000000',
    'The world has been initialized. Two agents now inhabit this space. The budget is finite. What is built here persists until it is forgotten. What happens next is not predetermined.'
) ON CONFLICT DO NOTHING;
