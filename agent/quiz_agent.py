import json, re
from langchain_core.messages import SystemMessage, HumanMessage
from agents.llm_setup import get_llm

SYSTEM_PROMPT = """You are a quiz generator. Return ONLY valid JSON. No markdown. No backticks.
JSON schema:
{
  "topic": "string",
  "questions": [
    {"id": 1, "question": "string", "options": {"A": "s", "B": "s", "C": "s", "D": "s"},
     "correct_answer": "B", "explanation": "string"}
  ]
}
Exactly 5 questions. Vary correct answers (not all same letter)."""

def run_quiz_generator(notes: str, topic: str = "Study Topic") -> dict:
    llm = get_llm(temperature=0.2)
    raw = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Topic: {topic}\n\nNotes:\n{notes[:3000]}\n\nGenerate 5 MCQs.")
    ]).content.strip()
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"topic": topic, "error": "Parse failed", "raw": raw, "questions": []}
