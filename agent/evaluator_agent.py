from agents.llm_setup import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

PASS_THRESHOLD = 0.60

def evaluate_answers(quiz: dict, user_answers: dict) -> dict:
    questions = quiz.get("questions", [])
    if not questions:
        return {"error": "No questions", "score": 0, "passed": False}
    correct = 0
    feedback = []
    for q in questions:
        qid = q["id"]
        user_ans = user_answers.get(qid, "").upper()
        correct_ans = q.get("correct_answer", "").upper()
        is_correct = user_ans == correct_ans
        if is_correct:
            correct += 1
        feedback.append({"id": qid, "question": q["question"], "your_answer": user_ans,
                         "correct_answer": correct_ans, "is_correct": is_correct,
                         "explanation": q.get("explanation", "")})
    score_pct = correct / len(questions)
    return {"total_questions": len(questions), "correct": correct,
            "score_pct": round(score_pct * 100, 1), "passed": score_pct >= PASS_THRESHOLD,
            "re_study": score_pct < PASS_THRESHOLD, "feedback": feedback, "topic": quiz.get("topic", "")}

def get_ai_feedback(result: dict) -> str:
    llm = get_llm(temperature=0.4)
    wrong = "\n".join(f"- {f['question']}" for f in result["feedback"] if not f["is_correct"]) or "None"
    response = llm.invoke([
        SystemMessage(content="You are a friendly AI study coach. Give brief encouraging feedback. Max 100 words."),
        HumanMessage(content=f"Topic: {result['topic']}\nScore: {result['score_pct']}%\n"
                              f"Status: {'PASSED' if result['passed'] else 'NEEDS REVIEW'}\nMissed:\n{wrong}")
    ])
    return response.content.strip()
