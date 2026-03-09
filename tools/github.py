import requests
from config.settings import settings

_BASE = "https://api.github.com"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }


def _repo() -> str:

    return f"{_BASE}/repos/{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}"


def gh_create_pr(branch: str, title: str, body: str = "") -> dict:

    resp = requests.post(
        f"{_repo()}/pulls",
        headers=_headers(),
        json={"title": title, "head": branch, "base": "main", "body": body},
        timeout=15,
    )

    resp.raise_for_status()
    data = resp.json()
    return {"number": data["number"], "url": data["html_url"]}


def gh_create_review(pr_number: int, body: str, approved: bool) -> dict:

    event = "APPROVE" if approved else "REQUEST_CHANGES"

    resp = requests.post(
        f"{_repo()}/pulls/{pr_number}/reviews",
        headers=_headers(),
        json={"body": body, "event": event},
        timeout=15,
    )

    resp.raise_for_status()
    return {"state": event}


def gh_create_comment(pr_number: int, body: str) -> dict:

    resp = requests.post(
        f"{_repo()}/issues/{pr_number}/comments",
        headers=_headers(),
        json={"body": body},
        timeout=15,
    )

    resp.raise_for_status()
    return {"id": resp.json()["id"]}


def gh_close_pr(pr_number: int) -> dict:

    resp = requests.patch(
        f"{_repo()}/pulls/{pr_number}",
        headers=_headers(),
        json={"state": "closed"},
        timeout=15,
    )

    resp.raise_for_status()
    return {"state": "closed"}


def gh_merge_pr(pr_number: int, message: str = "") -> dict:

    resp = requests.put(
        f"{_repo()}/pulls/{pr_number}/merge",
        headers=_headers(),
        json={"commit_message": message, "merge_method": "merge"},
        timeout=15,
    )

    resp.raise_for_status()
    
    return {"merged": True}