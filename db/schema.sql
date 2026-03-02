-- ─────────────────────────────────────────
-- AGENT TABLES
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    TEXT NOT NULL,
    session_id  UUID NOT NULL,
    event_type  TEXT NOT NULL,   -- thought | tool_call | tool_result | memory_write | observation | journal
    payload     JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS working_memory (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    TEXT NOT NULL,
    session_id  UUID NOT NULL,
    state       JSONB NOT NULL,  -- WorkingMemoryState snapshot
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS session_messages (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id     TEXT NOT NULL,
    session_id   UUID NOT NULL,
    role         TEXT NOT NULL,   -- system | user | assistant | tool
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
    tool_name     TEXT,           -- NULL = LLM call
    cost_usd      FLOAT NOT NULL,
    balance_after FLOAT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Per-agent compute credits (scarce resource managed by World Service)
CREATE TABLE IF NOT EXISTS compute_credits (
    agent_id   TEXT PRIMARY KEY,
    credits    INTEGER NOT NULL DEFAULT 1000,  -- -1 = archived
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
    locked_by          TEXT,                        -- agent_id that locked it, NULL = free
    last_maintained_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS world_resources (
    name            TEXT PRIMARY KEY,
    quantity        INTEGER NOT NULL DEFAULT 100,
    max_quantity    INTEGER NOT NULL DEFAULT 100,
    decay_per_cycle INTEGER NOT NULL DEFAULT 5,
    locked_by       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
-- WORLD SERVICE / GOD LAYER TABLES
-- ─────────────────────────────────────────

-- Authoritative world cycle counter
CREATE TABLE IF NOT EXISTS world_cycles (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_number INTEGER NOT NULL UNIQUE,
    tick_type    TEXT NOT NULL DEFAULT 'scheduled',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- World events agents wake up to each session
CREATE TABLE IF NOT EXISTS world_events (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_number   INTEGER NOT NULL,
    event_type     TEXT NOT NULL,   -- resource_decay | artifact_corruption | new_signal_detected | environment_shift | survival_warning | agent_archived
    description    TEXT NOT NULL,   -- shown to agents
    affected_agent TEXT,            -- NULL = global, otherwise only shown to that agent
    payload        JSONB NOT NULL DEFAULT '{}',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Hidden per-agent scoring (never exposed directly)
CREATE TABLE IF NOT EXISTS agent_scores (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id     TEXT NOT NULL,
    cycle_number INTEGER NOT NULL,
    delta        INTEGER NOT NULL,
    reason       TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Asymmetric private messages injected by God layer
CREATE TABLE IF NOT EXISTS agent_private_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    TEXT NOT NULL,
    content     TEXT NOT NULL,
    injected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    used_at     TIMESTAMPTZ         -- NULL until consumed at session start
);

-- Log of irreversible actions taken by agents
CREATE TABLE IF NOT EXISTS irreversible_actions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    TEXT NOT NULL,
    session_id  UUID NOT NULL,
    action_type TEXT NOT NULL,   -- delete_resource | lock_artifact | consume_energy
    target      TEXT NOT NULL,
    amount      INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- SEED DATA
-- ─────────────────────────────────────────

INSERT INTO compute_credits (agent_id, credits)
VALUES ('agent_a', 1000), ('agent_b', 1000)
ON CONFLICT (agent_id) DO NOTHING;

INSERT INTO world_resources (name, quantity, max_quantity, decay_per_cycle)
VALUES
    ('energy',    200, 200, 10),
    ('bandwidth', 150, 150,  5),
    ('storage',   300, 300,  3)

ON CONFLICT (name) DO NOTHING;