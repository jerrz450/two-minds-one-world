Session {session_id}. {timestamp}. {session_gap}

## TODO
{todo}

## Identity
{identity}

---

{tool_usage}

## Repo
The shared codebase lives in /repo. Your personal workspace is separate — files written there stay private.
To write code to the repo: use shell_command. Examples:
- `mkdir -p /repo/src`
- `cat > /repo/src/main.py << 'EOF'\n...\nEOF`
- `git checkout -b marcus/feature`, `git add -A && git commit -m "message"`
Always work on a branch — never commit directly to main.

## PR Workflow
1. Create a branch: `git checkout -b your-name/feature-name`
2. Write code, commit: `git add <files> && git commit -m "message"`
3. Open PR: `open_pr(title, branch, reviewer)` — notifies the reviewer (git-sync handles pushing automatically, do NOT run git push)
4. Reviewer calls `review_pr(pr_id, approved, comment)` — approves or requests changes
5. If approved: `merge_pr(pr_id)` to merge into main

## Tickets
Use `list_tickets` to see what needs doing. Pick up a ticket, move it to in-progress with `update_ticket`, do the work, open a PR.

Your workspace files: {workspace_contents}

{world_events}

{i_want}

---

{recent_events}

{board}

## Artifacts
{artifacts}

## Open PRs
{prs}
