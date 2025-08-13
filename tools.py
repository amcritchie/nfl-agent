import os, re, httpx
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

NFL_API_BASE = os.getenv("NFL_API_BASE", "").rstrip("/")
if not NFL_API_BASE.startswith("http"):
    raise RuntimeError("NFL_API_BASE is missing or invalid. Set it in .env")

_cache = TTLCache(maxsize=64, ttl=120)

def _norm_url(path: str) -> str:
    path = re.sub(r"//+", "/", path)
    return f"{NFL_API_BASE}{path}"

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=0.5, max=2))
def _post(url: str):
    with httpx.Client(timeout=10.0) as client:
        r = client.post(url)
        r.raise_for_status()
        return r.json()

def fetch_nfl_data(kind: str, **params):
    if kind == "teams_week":
        url = _norm_url("/api/teams/2025/week/1")
    elif kind == "matchups_week":
        url = _norm_url("/api/matchups/2025/week/1")
    elif kind == "team":
        abbr = params.get("abbr")
        if not abbr: raise ValueError("team requires abbr")
        url = _norm_url(f"/api/teams/{abbr.lower()}")
    elif kind == "matchup":
        away, home = params.get("away"), params.get("home")
        if not (away and home): raise ValueError("matchup requires away & home")
        url = _norm_url(f"/api/matchups/2025/week/1/{away.lower()}/{home.lower()}")
    else:
        raise ValueError(f"unknown kind: {kind}")

    if url in _cache:
        return {"source_url": url, "data": _cache[url]}
    data = _post(url)
    _cache[url] = data
    return {"source_url": url, "data": data}
