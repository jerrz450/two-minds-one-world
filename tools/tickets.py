import json
import uuid
from psycopg2.extras import RealDictCursor
from config.clients import get_db, get_redis
from tools.github import gh_create_pr, gh_create_review, gh_create_comment, gh_close_pr, gh_merge_pr

def _notify(to: str, from_agent: str, content: str) -> None:
    get_redis().publish("messages:outbox", json.dumps({"type": "dm", "from": from_agent, "to": to, "content": content}))

def _get_pr(pr_id: str) -> dict | None:

    with get_db() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM pull_requests WHERE id = %s", (pr_id,))
            row = cur.fetchone()

    return dict(row) if row else None

def create_ticket(agent_id: str, session_id: str, title: str, description: str | None = None, assignee: str | None = None) -> dict:
    
    ticket_id = f"T-{str(uuid.uuid4())[:8].upper()}"

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tickets (id, title, description, assignee, created_by) VALUES (%s, %s, %s, %s, %s)",
                (ticket_id, title, description, assignee, agent_id),
            )
    
    if assignee:
        _notify(assignee, agent_id, f"Ticket {ticket_id} assigned to you: {title}")

    return {"id": ticket_id, "title": title, "assignee": assignee}


def update_ticket(agent_id: str, session_id: str, ticket_id: str, status: str | None = None, assignee: str | None = None) -> dict:
    
    with get_db() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute("UPDATE tickets SET status = %s WHERE id = %s", (status, ticket_id))

            if assignee:
                cur.execute("UPDATE tickets SET assignee = %s WHERE id = %s", (assignee, ticket_id))

    return {"id": ticket_id, "updated": True}


def list_tickets(agent_id: str, session_id: str, status: str | None = None) -> list[dict]:

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            if status:
                cur.execute("SELECT id, title, status, assignee, created_by FROM tickets WHERE status = %s ORDER BY created_at ASC", (status,))
            else:
                cur.execute("SELECT id, title, status, assignee, created_by FROM tickets ORDER BY created_at ASC")

            return [dict(r) for r in cur.fetchall()]


def open_pr(agent_id: str, session_id: str, title: str, branch: str, reviewer: str, ticket_id: str | None = None, description: str = "") -> dict:

    try:

        gh = gh_create_pr(branch, title, description)

    except Exception as e:
        return {"error": str(e)}

    pr_id = f"PR-{str(uuid.uuid4())[:8].upper()}"
    
    with get_db() as conn:
        with conn.cursor() as cur:
         cur.execute(
            
                "INSERT INTO p      ull_requests (id, branch, title, author, reviewer, ticket_id, gh_number, gh_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (pr_id, branch, title, agent_id, reviewer, ticket_id, gh["number"], gh["url"]),
            )

    _notify(reviewer, agent_id, f"Review requested: {title} — {gh['url']}")
    return {"id": pr_id, "gh_url": gh["url"], "reviewer": reviewer}


def review_pr(agent_id: str, session_id: str, pr_id: str, approved: bool, comment: str = "") -> dict:
    
    pr = _get_pr(pr_id)

    if not pr:
        return {"error": f"PR {pr_id} not found"}
    
    try:
        gh_create_review(pr["gh_number"], comment, approved)

    except Exception as e:
        return {"error": str(e)}
    
    status = "approved" if approved else "changes_requested"

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE pull_requests SET status = %s WHERE id = %s", (status, pr_id))

            if comment:
                cur.execute("INSERT INTO pr_comments (pr_id, agent_id, content) VALUES (%s, %s, %s)", (pr_id, agent_id, comment))
   
    _notify(pr["author"], agent_id, f"{pr_id} {'approved' if approved else 'needs changes'}: {comment}")
    return {"id": pr_id, "status": status}


def comment_pr(agent_id: str, session_id: str, pr_id: str, content: str) -> dict:

    pr = _get_pr(pr_id)

    if not pr:
        return {"error": f"PR {pr_id} not found"}
    try:
        gh_create_comment(pr["gh_number"], f"**{agent_id}**: {content}")

    except Exception as e:
        return {"error": str(e)}
    
    with get_db() as conn:

        with conn.cursor() as cur:
            cur.execute("INSERT INTO pr_comments (pr_id, agent_id, content) VALUES (%s, %s, %s)", (pr_id, agent_id, content))
    return {"pr_id": pr_id, "status": "commented"}


def merge_pr(agent_id: str, session_id: str, pr_id: str) -> dict:

    pr = _get_pr(pr_id)

    if not pr:
        return {"error": f"PR {pr_id} not found"}
    
    if pr["status"] != "approved":
        return {"error": "PR is not approved"}
    
    try:
        gh_merge_pr(pr["gh_number"])

    except Exception as e:
        return {"error": str(e)}
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE pull_requests SET status = 'merged' WHERE id = %s", (pr_id,))

    _notify(pr["author"], agent_id, f"{pr_id} merged.")
    return {"id": pr_id, "status": "merged"}


def close_pr(agent_id: str, session_id: str, pr_id: str, reason: str = "") -> dict:

    pr = _get_pr(pr_id)

    if not pr:
        return {"error": f"PR {pr_id} not found"}
    try:
        if reason:
            gh_create_comment(pr["gh_number"], f"Closing: {reason}")
        gh_close_pr(pr["gh_number"])

    except Exception as e:
        return {"error": str(e)}
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE pull_requests SET status = 'closed' WHERE id = %s", (pr_id,))

    _notify(pr["author"], agent_id, f"{pr_id} closed. {reason}")

    return {"id": pr_id, "status": "closed"}


def list_prs(agent_id: str, session_id: str, status: str | None = None) -> list[dict]:

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            if status:
                cur.execute("SELECT id, title, branch, author, reviewer, status, ticket_id, gh_url FROM pull_requests WHERE status = %s ORDER BY created_at ASC", (status,))
            else:
                cur.execute("SELECT id, title, branch, author, reviewer, status, ticket_id, gh_url FROM pull_requests ORDER BY created_at ASC")
            
            return [dict(r) for r in cur.fetchall()]
