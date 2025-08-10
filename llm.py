import os, re
PROVIDER = os.getenv("LLM_PROVIDER", "none").lower()
MODEL = os.getenv("LLM_MODEL", "")

TEAMS = r"(ari|atl|bal|buf|car|chi|cin|cle|dal|den|det|gb|hou|ind|jax|kc|lv|lac|lar|mia|min|ne|no|nyg|nyj|phi|pit|sea|sf|tb|ten|was)"

def call_llm(messages, tools_schema=True):
    # MVP heuristic router when PROVIDER=none
    user = messages[-1]["content"].lower()
    if "matchup" in user or " vs " in user or " @ " in user:
        m = re.findall(TEAMS, user)
        if len(m) >= 2:
            return {"tool_call": {"name": "fetch_nfl_data",
                                  "arguments": {"kind":"matchup","away":m[0],"home":m[1]}}}
        return {"tool_call": {"name": "fetch_nfl_data", "arguments": {"kind":"matchups_week"}}}
    if "home teams" in user or ("week 1" in user and "home" in user):
        return {"tool_call": {"name": "fetch_nfl_data", "arguments": {"kind":"matchups_week"}}}
    if any(k in user for k in ["starting","starter","lt","qb","wr","left tackle"]):
        m = re.search(TEAMS, user)
        abbr = m.group(1) if m else "phi"
        return {"tool_call": {"name": "fetch_nfl_data", "arguments": {"kind":"team","abbr":abbr}}}
    return {"tool_call": {"name": "fetch_nfl_data", "arguments": {"kind":"teams_week"}}}
