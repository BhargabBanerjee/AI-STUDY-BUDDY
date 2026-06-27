"""
graph.py — LangGraph StateGraph pipeline (lives in root folder, NOT in app/)
"""
from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents.planner_agent import run_planner
from agents.researcher_agent import run_researcher
from agents.quiz_agent import run_quiz_generator
from agents.evaluator_agent import evaluate_answers, get_ai_feedback
from memory.memory_store import save_note, add_to_history

MAX_RETRIES = 2

class StudyState(TypedDict):
    topic: str
    plan: dict
    current_subtopic: str
    notes: str
    quiz: dict
    user_answers: dict
    eval_result: dict
    ai_feedback: str
    retry_count: int
    status: str
    error_message: str

def plan_node(state):
    try:
        plan = run_planner(state["topic"])
        add_to_history("system", f"Generated plan for: {state['topic']}")
        return {**state, "plan": plan, "status": "researching"}
    except Exception as e:
        return {**state, "status": "error", "error_message": str(e)}

def research_node(state):
    try:
        subtopic = state.get("current_subtopic") or state["topic"]
        notes = run_researcher(subtopic)
        save_note(subtopic=subtopic, notes=notes, topic=state["topic"])
        add_to_history("system", f"Researched: {subtopic}")
        return {**state, "notes": notes, "status": "quizzing"}
    except Exception as e:
        return {**state, "status": "error", "error_message": str(e)}

def quiz_node(state):
    try:
        quiz = run_quiz_generator(notes=state["notes"], topic=state.get("current_subtopic") or state["topic"])
        return {**state, "quiz": quiz, "status": "evaluating"}
    except Exception as e:
        return {**state, "status": "error", "error_message": str(e)}

def evaluate_node(state):
    try:
        result = evaluate_answers(state["quiz"], state["user_answers"])
        feedback = get_ai_feedback(result)
        add_to_history("assistant", f"Quiz score: {result['score_pct']}%")
        return {**state, "eval_result": result, "ai_feedback": feedback,
                "status": "done" if result["passed"] else "needs_review"}
    except Exception as e:
        return {**state, "status": "error", "error_message": str(e)}

def route_after_eval(state):
    if state["status"] == "error":
        return END
    if state["status"] == "needs_review" and state.get("retry_count", 0) < MAX_RETRIES:
        return "research"
    return END

def build_graph():
    builder = StateGraph(StudyState)
    builder.add_node("plan", plan_node)
    builder.add_node("research", research_node)
    builder.add_node("quiz", quiz_node)
    builder.add_node("evaluate", evaluate_node)
    builder.set_entry_point("plan")
    builder.add_edge("plan", "research")
    builder.add_edge("research", "quiz")
    builder.add_edge("quiz", "evaluate")
    builder.add_conditional_edges("evaluate", route_after_eval, {"research": "research", END: END})
    return builder.compile()

compiled_graph = build_graph()
