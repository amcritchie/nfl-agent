from dotenv import load_dotenv; load_dotenv()

import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tools import fetch_nfl_data
from prompts import SYSTEM_PROMPT
from llm import call_llm

app = FastAPI(title="NFL Week1 Agent")

class AskIn(BaseModel):
    question: str

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/ask")
def ask(body: AskIn):
    messages = [
        {"role":"system","content": SYSTEM_PROMPT},
        {"role":"user","content": body.question}
    ]
    decision = call_llm(messages, tools_schema=True)
    sources = []
    if "tool_call" in decision:
        tc = decision["tool_call"]
        if tc["name"] != "fetch_nfl_data":
            raise HTTPException(status_code=400, detail="Unknown tool requested")
        tool_result = fetch_nfl_data(**tc["arguments"])
        sources.append(tool_result["source_url"])
        # MVP reply; swap to real LLM later for synthesis
        answer = f"I fetched data from {tool_result['source_url']}. What detail do you want (starters, positions, strengths)?"
    else:
        answer = "Ask me about a team or matchup for Week 1."
    return {"answer": answer, "sources": sources}
