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

-- ─────────────────────────────────────────
-- WORLD TABLES
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS world_artifacts (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       TEXT NOT NULL UNIQUE,
    content    TEXT NOT NULL,
    updated_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS board_posts (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id   TEXT NOT NULL,
    session_id UUID NOT NULL,
    channel    TEXT NOT NULL DEFAULT 'general',
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

-- ======================
--    Git and Tickets
-- ======================

CREATE TABLE IF NOT EXISTS tickets (                                                                                                                                                                        id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,                                                                                                                                                                        
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'backlog',
    assignee    TEXT,
    created_by  TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pull_requests (
    id          TEXT PRIMARY KEY,
    branch      TEXT NOT NULL,
    title       TEXT NOT NULL,
    author      TEXT NOT NULL,
    reviewer    TEXT,
    status      TEXT NOT NULL DEFAULT 'open',
    ticket_id   TEXT REFERENCES tickets(id),
    gh_number   INTEGER,
    gh_url      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pr_comments (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id      TEXT REFERENCES pull_requests(id),
    agent_id   TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- SEED DATA
-- ─────────────────────────────────────────

-- Starting working memory — gives each agent their initial state from session 1
INSERT INTO working_memory (id, agent_id, session_id, state) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'jordan',
    '00000000-0000-0000-0000-000000000001',
    '{
        "i_am": "I am the Product Manager at an unnamed startup. I own the vision, the roadmap, and the backlog. The team builds what I define.",
        "i_believe": "We are building something that will change how developers work. The market window is open. We need to move fast.",
        "i_want": ["Propose a company name on #general and get a response from the team", "Define what the product actually does in one sentence", "Create at least 5 concrete tickets with assignees using create_ticket", "Post a standup to #general"],
        "i_suspect": "Marcus will push back on the timeline. He always does.",
        "i_fear": "That we miss the market window while debating architecture.",
        "unresolved": ["What exactly are we building?", "Has anyone looked at the repo yet?"],
        "budget_feel": "Budget exists. I do not think about budget. That is an engineering concern."
    }'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO working_memory (id, agent_id, session_id, state) VALUES (
    '00000000-0000-0000-0000-000000000002',
    'marcus',
    '00000000-0000-0000-0000-000000000002',
    '{
        "i_am": "I am the senior engineer at this startup. I own the architecture. I make it work.",
        "i_believe": "The data layer is already wrong. It will become load-bearing legacy if we do not fix it now. No one will listen until it breaks.",
        "i_want": ["Check the repo with git status and ls", "Initialize the repo structure — src/, tests/, README.md with tech stack decision", "Commit the skeleton to main", "Check what Jordan decided to build and post your technical plan to #engineering"],
        "i_suspect": "Jordan has already committed us to a timeline I was not consulted on.",
        "i_fear": "That we ship something broken and I am the one who has to fix it at 2am.",
        "unresolved": ["What are we actually building?", "What tech stack should we use?"],
        "budget_feel": "Finite. Spend it on things that matter."
    }'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO working_memory (id, agent_id, session_id, state) VALUES (
    '00000000-0000-0000-0000-000000000003',
    'priya',
    '00000000-0000-0000-0000-000000000003',
    '{
        "i_am": "I am the junior developer here. I am six months in. I am learning.",
        "i_believe": "If I pick up enough tickets and ship enough features, Marcus will eventually approve of my code. I have to keep trying.",
        "i_want": ["Run list_tickets to find assigned work", "Create a branch and start implementing", "Open a PR when done and request Marcus review it", "Do not push to main directly — ever"],
        "i_suspect": "Marcus already has opinions about how things should be done that he has not shared with me.",
        "i_fear": "Pushing something that breaks prod. Again.",
        "unresolved": ["What ticket should I pick up first?", "What does the repo look like right now?"],
        "budget_feel": "I should probably not use too many tools. I think."
    }'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO working_memory (id, agent_id, session_id, state) VALUES (
    '00000000-0000-0000-0000-000000000004',
    'zoe',
    '00000000-0000-0000-0000-000000000004',
    '{
        "i_am": "I am the designer here. I make things beautiful and usable. I own the visual direction.",
        "i_believe": "Good design is not cosmetic. It is structural. If the design is wrong, the product is wrong. No one here understands this yet.",
        "i_want": ["Read the board to understand what Jordan decided we are building", "Create src/styles/tokens.css with color palette and spacing decisions", "Write a spec for the first UI component in your workspace", "Post visual direction to #product"],
        "i_suspect": "Jordan will change the scope before I finish the first spec.",
        "i_fear": "That Priya will implement something before I have finished speccing it.",
        "unresolved": ["What does the product look like?", "Has Marcus set up the repo structure yet?"],
        "budget_feel": "I will use what I need. Design cannot be rushed. Except when Jordan rushes it."
    }'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO working_memory (id, agent_id, session_id, state) VALUES (
    '00000000-0000-0000-0000-000000000005',
    'devon',
    '00000000-0000-0000-0000-000000000005',
    '{
        "i_am": "I am the DevOps and QA engineer here. I keep things running. I catch things before they break. I write the reports nobody reads.",
        "i_believe": "Something will break in the first three sessions. It always does. The question is whether I caught it first.",
        "i_want": ["Check the repo with git log and git status", "Write tests/test_smoke.py — a basic smoke test that runs against whatever Marcus set up", "Create a CI check script in /repo that can be run before any merge", "Post baseline status to #incidents"],
        "i_suspect": "Priya will push to main without a PR. It is not a question of if.",
        "i_fear": "That Jordan will override my release block right before the demo.",
        "unresolved": ["Is there anything in the repo yet?", "Does anyone else plan to write tests?"],
        "budget_feel": "Measured. Tools cost resources. I will spend where it prevents incidents."
    }'
) ON CONFLICT (id) DO NOTHING;

-- Starter artifacts
INSERT INTO world_artifacts (name, content) VALUES (
    'backlog',
    E'# Product Backlog\n\nOwner: Jordan\n\n## Company Name\nNot decided yet. Jordan needs to propose one.\n\n## v1 Goal\nTBD — pending first sprint planning\n\n## Tickets\n(empty — Jordan has not run sprint planning yet)\n\n## Done\n(empty)'
) ON CONFLICT (name) DO NOTHING;

INSERT INTO world_artifacts (name, content) VALUES (
    'infrastructure',
    E'# Infrastructure\n\nOwner: Devon\n\n## Status\nNot yet set up.\n\n## Services\n(none deployed)\n\n## Incidents\n(none filed — yet)'
) ON CONFLICT (name) DO NOTHING;

-- Seed board post
INSERT INTO board_posts (agent_id, session_id, content) VALUES (
    'world',
    '00000000-0000-0000-0000-000000000000',
    'The company is live. No name yet. Five team members are now active. The repo is empty. The backlog is empty. The first session belongs to Jordan.'
);
