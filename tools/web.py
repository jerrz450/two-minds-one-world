import html2text
import requests
from duckduckgo_search import DDGS

_PAGE_CAP = 6000  # max chars returned from a fetched page

def web_search(query: str, max_results: int = 5) -> list[dict]:
    
    """Search the web via DuckDuckGo. Returns title, url, snippet."""

    try:
        results = DDGS().text(query, max_results=max_results)
        return [{"title": r["title"], "url": r["href"], "snippet": r["body"]} for r in results]
    
    except Exception as e:
        return [{"error": str(e)}]


def fetch_url(url: str) -> dict:
    
    """Fetch a web page and return its text content."""

    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        text = h.handle(resp.text)

        return {"url": url, "content": text[:_PAGE_CAP]}
    
    except Exception as e:
        return {"error": str(e)}
