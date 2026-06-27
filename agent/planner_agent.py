import json, re
from langchain_core.messages import SystemMessage, HumanMessage
from agents.llm_setup import get_llm

SYSTEM_PROMPT = """You are a study planner AI. Return ONLY valid JSON. No markdown. No backticks.
JSON schema:
{
  "topic": "string",
  "total_days": 5,
  "days": [
    {"day": 1, "title": "string", "goal": "string", "subtopics": ["string"], "resources": ["string"]}
  ]
}"""

def run_planner(topic: str) -> dict:
    llm = get_llm(temperature=0.1)
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT),
                           HumanMessage(content=f"Create a 5-day study plan for: {topic}")])
    raw = re.sub(r"```(?:json)?", "", response.content.strip()).strip().rstrip("`").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"topic": topic, "error": "Parse failed", "raw": raw, "total_days": 0, "days": []}
