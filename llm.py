import os, re
from openai import OpenAI
from typing import Dict, Any, List

PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Tool schema for fetch_nfl_data
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "fetch_nfl_data",
            "description": "Fetch NFL data from the API",
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["teams_week", "matchups_week", "team", "matchup"],
                        "description": "Type of data to fetch"
                    },
                    "abbr": {
                        "type": "string",
                        "description": "Team abbreviation (required for 'team' kind)"
                    },
                    "away": {
                        "type": "string",
                        "description": "Away team abbreviation (required for 'matchup' kind)"
                    },
                    "home": {
                        "type": "string",
                        "description": "Home team abbreviation (required for 'matchup' kind)"
                    }
                },
                "required": ["kind"]
            }
        }
    }
]

def call_llm(messages: List[Dict[str, str]], tools_schema: bool = True) -> Dict[str, Any]:
    print(f"step 1")
    """Call OpenAI GPT-4o-mini with tool calling capabilities"""
    
    if PROVIDER == "none":
        print(f"step2.1")
        # Fallback to MVP heuristic router for testing
        return _fallback_heuristic(messages[-1]["content"])
    
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required when using OpenAI provider")
    
    print(f"step2.2")
    client = OpenAI(api_key=OPENAI_API_KEY)
    print(f"step2.3 - MODEL - {MODEL}")
    try:
        print(f"step2.4")
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages
            # tools=TOOLS_SCHEMA if tools_schema else None,
            # tool_choice="auto" if tools_schema else None,
            # temperature=0.1,
            # max_tokens=1000
        )
        print(f"step2.5")
        print(f"client - {client}")
        print(f"Response - {response}")
        print(f"Response - {response.choices[0]}")
        
        choice = response.choices[0]
        
        if tools_schema and choice.message.tool_calls:
            # Return tool call information
            tool_call = choice.message.tool_calls[0]
            return {
                "tool_call": {
                    "name": tool_call.function.name,
                    "arguments": eval(tool_call.function.arguments)
                }
            }
        else:
            # Return the text response
            return {"content": choice.message.content}
            
    except Exception as e:
        # Fallback to heuristic if OpenAI fails
        print(f"OpenAI call failed: {e}")
        return _fallback_heuristic(messages[-1]["content"])

def _fallback_heuristic(user_content: str) -> Dict[str, Any]:
    """Fallback heuristic router for when OpenAI is unavailable"""
    TEAMS = r"(ari|atl|bal|buf|car|chi|cin|cle|dal|den|det|gb|hou|ind|jax|kc|lv|lac|lar|mia|min|ne|no|nyg|nyj|phi|pit|sea|sf|tb|ten|was)"
    
    user = user_content.lower()
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
