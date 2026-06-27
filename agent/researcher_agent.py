import os
from langchain_core.messages import SystemMessage, HumanMessage
from agents.llm_setup import get_llm

SYSTEM_PROMPT = """You are a research assistant. Write clear study notes for students.
Format:
## <Subtopic Title>
**Key Concepts:** bullet points
**Explanation:** 2-3 paragraphs
**Key Takeaways:** 3-5 bullets
Always respond in English."""

def _tavily_search(query: str) -> str:
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return ""
    try:
        from tavily import TavilyClient
        results = TavilyClient(api_key=api_key).search(query=query, max_results=3)
        return "\n\n".join(r.get("content", "") for r in results.get("results", []))[:2000]
    except Exception:
        return ""

def run_researcher(subtopic: str) -> str:
    llm = get_llm(temperature=0.3)
    web = _tavily_search(subtopic)
    context = f"\n\nWeb research:\n{web}" if web else ""
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Write study notes for: '{subtopic}'{context}")
    ])
    return response.content.strip()
