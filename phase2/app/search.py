"""Optional web search. Results are snippets, never verified product facts."""

import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


def should_search(message):
    if not os.environ.get("PHASE2_SEARCH_API_KEY"):
        return False
    fresh_terms = ("가격", "최저가", "재고", "판매", "후기", "리뷰", "스펙", "비교", "검색", "찾아", "추천")
    return any(term in message for term in fresh_terms)


def search_web(query):
    """Return at most three sourced Brave web snippets, or raise on failure."""
    key = os.environ.get("PHASE2_SEARCH_API_KEY")
    if not key:
        return []
    endpoint = os.environ.get("PHASE2_SEARCH_API_URL", "https://api.search.brave.com/res/v1/web/search")
    url = endpoint + ("&" if "?" in endpoint else "?") + urlencode({"q": query[:300], "count": 3})
    request = Request(url, headers={"X-Subscription-Token": key, "Accept": "application/json"})
    with urlopen(request, timeout=12) as response:
        data = json.load(response)
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = []
    for item in data.get("web", {}).get("results", [])[:3]:
        link = item.get("url", "")
        parsed = urlsplit(link)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            continue
        results.append({"url": link[:1000], "title": str(item.get("title", ""))[:150],
                        "snippet": str(item.get("description", ""))[:500],
                        "checked_at": checked_at, "verification": "search_snippet_unverified"})
    return results
