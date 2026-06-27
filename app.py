"""
app.py — AI Study Buddy (Updated)
Run: streamlit run app.py

New Features:
  • 💬 Chatbot: unlimited multi-turn, JSON memory, file uploads (PDF/image/audio)
  • 📚 Chat History panel in sidebar
  • 🔬 Multi-Question Research planner (fresh independent answers)
  • 📋 5-day Study Plan + Quiz system (unchanged)
"""
import os
import json
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; }
    .study-card { background:#1e293b; border:1px solid #334155; border-radius:12px; padding:18px 20px; margin-bottom:12px; color:#e2e8f0; }
    .study-card h4 { color:#7dd3fc; margin:0 0 6px 0; font-size:0.95rem; }
    .chat-user { background:#1e3a5f; border-radius:12px 12px 4px 12px; padding:10px 14px; margin:6px 0; color:#e2e8f0; }
    .chat-assistant { background:#1e293b; border-radius:12px 12px 12px 4px; padding:10px 14px; margin:6px 0; color:#e2e8f0; border-left:3px solid #7dd3fc; }
    .chat-meta { font-size:0.72rem; color:#64748b; margin-top:4px; }
    .history-item { background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:8px 10px; margin:4px 0; cursor:pointer; }
    .history-item:hover { border-color:#7dd3fc; }
    .file-badge { background:#0f4c81; border-radius:6px; padding:2px 8px; font-size:0.8rem; color:#7dd3fc; display:inline-block; margin:2px; }
</style>
""", unsafe_allow_html=True)


# ── State ──────────────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "stage": "home",
        "topic": "",
        "plan": {},
        "selected_day": 1,
        "current_subtopic": "",
        "notes": "",
        "quiz": {},
        "user_answers": {},
        "eval_result": {},
        "ai_feedback": "",
        "retry_count": 0,
        "provider": os.getenv("LLM_PROVIDER", "mistral").capitalize(),
        # Chatbot
        "chat_messages": [],          # in-session display list
        "show_history": False,
        # Research
        "research_questions": [""],
        "research_results": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 AI Study Buddy")
    st.caption(f"Powered by **{st.session_state.provider}**")
    st.divider()

    provider_choice = st.selectbox(
        "🔌 LLM Provider",
        ["mistral", "gemini", "ollama"],
        index=["mistral", "gemini", "ollama"].index(os.getenv("LLM_PROVIDER", "mistral")),
    )
    if provider_choice != os.getenv("LLM_PROVIDER", "mistral"):
        os.environ["LLM_PROVIDER"] = provider_choice
        st.session_state.provider = provider_choice.capitalize()
        st.success(f"Switched to {provider_choice}!")

    st.divider()
    st.markdown("### 📍 Navigation")

    nav_buttons = [
        ("🏠 Home", "home"),
        ("💬 Chatbot", "chatbot"),
        ("🔬 Multi-Q Research", "multi_research"),
    ]
    for label, stage_key in nav_buttons:
        if st.button(label, use_container_width=True):
            st.session_state.stage = stage_key
            st.rerun()

    if st.session_state.plan:
        if st.button("📋 My Study Plan", use_container_width=True):
            st.session_state.stage = "plan"
            st.rerun()

    st.divider()

    # Chat History panel
    st.markdown("### 📜 Chat History")
    from memory.memory_store import load_chat_history
    history = load_chat_history()
    if history:
        if st.button("🗂️ View Full History", use_container_width=True):
            st.session_state.stage = "chat_history"
            st.rerun()
        st.caption(f"{len(history)} messages saved")
        # Preview last 3
        for msg in history[-3:]:
            role_icon = "🧑" if msg["role"] == "user" else "🤖"
            ts = msg.get("timestamp", "")[:16].replace("T", " ")
            preview = msg["content"][:60] + ("…" if len(msg["content"]) > 60 else "")
            st.markdown(f'<div class="history-item">{role_icon} <span style="font-size:0.8rem">{preview}</span><br><span style="font-size:0.7rem;color:#64748b">{ts}</span></div>', unsafe_allow_html=True)
    else:
        st.caption("No chat history yet")

    st.divider()
    try:
        from memory.memory_store import get_note_count
        st.metric("📚 Notes Saved", get_note_count())
    except Exception:
        st.caption("Memory: not initialized")

    st.divider()
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🔄 Reset Session", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    with col_r2:
        from memory.memory_store import clear_chat_history
        if st.button("🗑️ Clear Chat", use_container_width=True):
            clear_chat_history()
            st.session_state.chat_messages = []
            st.success("Chat cleared!")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.stage == "home":
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("# 🎓 AI Study Buddy")
        st.markdown("#### Your personal AI tutor — plans, researches, quizzes, chats, and tracks your learning.")
        st.markdown("### 🚀 What do you want to learn today?")
        topic_input = st.text_input("Enter a topic", placeholder="e.g. Machine Learning, Python, World War II...")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("📋 Generate Study Plan", type="primary", use_container_width=True):
                if topic_input.strip():
                    st.session_state.topic = topic_input.strip()
                    st.session_state.stage = "plan"
                    st.rerun()
                else:
                    st.warning("Please enter a topic first.")
        with col_b:
            if st.button("⚡ Quick Research", use_container_width=True):
                if topic_input.strip():
                    st.session_state.topic = topic_input.strip()
                    st.session_state.current_subtopic = topic_input.strip()
                    st.session_state.stage = "research"
                    st.rerun()
                else:
                    st.warning("Please enter a topic first.")
        with col_c:
            if st.button("💬 Open Chatbot", use_container_width=True):
                st.session_state.stage = "chatbot"
                st.rerun()

    with col2:
        st.markdown("### 📊 Features")
        for icon, step in [
            ("💬", "AI Chatbot — unlimited turns"),
            ("📎", "Upload PDF or Image"),
            ("🔬", "Multi-Question Research"),
            ("📋", "5-Day Study Planner"),
            ("🧠", "AI Quiz Generator"),
            ("📜", "Persistent Chat History"),
        ]:
            st.markdown(f'<div class="study-card"><h4>{icon} {step}</h4></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CHATBOT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "chatbot":
    from agents.chatbot_agent import run_chatbot
    from memory.memory_store import save_chat_message, load_chat_history

    st.markdown("## 💬 AI Study Chatbot")
    st.caption("Unlimited multi-turn conversation. Upload PDFs or images for analysis.")

    # File uploader
    uploaded_file = st.file_uploader(
        "📎 Attach a file (optional)",
        type=["pdf", "png", "jpg", "jpeg", "gif", "webp", "bmp", "txt"],
        help="Attach a PDF or image. The chatbot will analyze and summarize it.",
        key="chat_file_upload"
    )

    # Display chat messages
    st.divider()
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_messages:
            st.info("👋 Hi! I'm your AI Study Buddy. Ask me anything, or upload a file for analysis!")
        else:
            for msg in st.session_state.chat_messages:
                role = msg["role"]
                content = msg["content"]
                ts = msg.get("timestamp", "")
                if role == "user":
                    file_badge = f'<span class="file-badge">📎 {msg.get("file_name","")}</span>' if msg.get("file_name") else ""
                    st.markdown(f'<div class="chat-user">🧑 <strong>You</strong><br>{content}{file_badge}<div class="chat-meta">{ts}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-assistant">🤖 <strong>AI</strong><br>', unsafe_allow_html=True)
                    st.markdown(content)
                    st.markdown(f'<div class="chat-meta">{ts}</div></div>', unsafe_allow_html=True)

    st.divider()

    # Input area
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_area(
            "Your message",
            placeholder="Type your question here… (Shift+Enter for new line)",
            key="chat_input",
            height=80,
            label_visibility="collapsed"
        )
    with col_send:
        send_btn = st.button("Send 📨", type="primary", use_container_width=True, key="send_chat")

    if send_btn and user_input.strip():
        now = datetime.now().strftime("%H:%M")

        # Read file if attached
        file_bytes = None
        file_name = None
        file_type = None
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            file_name = uploaded_file.name
            file_type = uploaded_file.type

        # Add user message to session
        user_msg = {
            "role": "user",
            "content": user_input.strip(),
            "timestamp": now,
            "file_name": file_name,
        }
        st.session_state.chat_messages.append(user_msg)

        # Save user message to JSON
        save_chat_message(
            role="user",
            content=user_input.strip(),
            metadata={"file": file_name} if file_name else None
        )

        # Build conversation history for LLM (all prior messages, no file blobs)
        llm_history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.chat_messages[:-1]  # exclude the one we just added
        ]

        with st.spinner("🤖 Thinking…"):
            try:
                response = run_chatbot(
                    user_message=user_input.strip(),
                    conversation_history=llm_history,
                    uploaded_file_bytes=file_bytes,
                    uploaded_file_name=file_name,
                    uploaded_file_type=file_type,
                )
            except Exception as e:
                response = f"❌ Error: {e}"

        # Add assistant reply
        asst_msg = {"role": "assistant", "content": response, "timestamp": datetime.now().strftime("%H:%M")}
        st.session_state.chat_messages.append(asst_msg)
        save_chat_message(role="assistant", content=response)

        st.rerun()

    # Suggested prompts
    if not st.session_state.chat_messages:
        st.markdown("**💡 Try asking:**")
        sugg_cols = st.columns(3)
        suggestions = [
            "Explain neural networks simply",
            "What is quantum entanglement?",
            "Summarize the uploaded PDF",
        ]
        for i, s in enumerate(suggestions):
            with sugg_cols[i]:
                if st.button(s, key=f"sugg_{i}", use_container_width=True):
                    st.session_state.chat_input = s
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CHAT HISTORY VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "chat_history":
    from memory.memory_store import load_chat_history, clear_chat_history
    from memory.memory_store import CHAT_HISTORY_FILE

    st.markdown("## 📜 Chat History")
    history = load_chat_history()

    col1, col2, col3 = st.columns([3, 1, 1])
    with col2:
        if st.button("💬 Back to Chat", use_container_width=True):
            st.session_state.stage = "chatbot"
            st.rerun()
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True):
            clear_chat_history()
            st.session_state.chat_messages = []
            st.success("History cleared!")
            st.rerun()

    if not history:
        st.info("No chat history yet. Start a conversation in the Chatbot!")
    else:
        st.caption(f"Total messages: {len(history)}")
        st.divider()

        # Download button
        history_json = json.dumps(history, indent=2, ensure_ascii=False)
        st.download_button(
            label="⬇️ Download History (JSON)",
            data=history_json,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
        )
        st.divider()

        # Search/filter
        search_term = st.text_input("🔍 Search history", placeholder="Filter messages…")

        for msg in reversed(history):
            content = msg.get("content", "")
            if search_term and search_term.lower() not in content.lower():
                continue
            role = msg.get("role", "user")
            ts = msg.get("timestamp", "")[:19].replace("T", " ")
            meta = msg.get("metadata", {})
            icon = "🧑" if role == "user" else "🤖"
            label = "You" if role == "user" else "AI Study Buddy"
            file_info = f" · 📎 {meta.get('file')}" if meta and meta.get("file") else ""

            with st.expander(f"{icon} {label} — {ts}{file_info}"):
                st.markdown(content)


# ══════════════════════════════════════════════════════════════════════════════
# MULTI-QUESTION RESEARCH
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "multi_research":
    from agents.chatbot_agent import run_multi_question_research

    st.markdown("## 🔬 Multi-Question Research")
    st.caption("Enter multiple research questions. Each gets a fresh, independent, thorough answer.")

    # Dynamic question list
    questions = st.session_state.research_questions

    st.markdown("### 📝 Your Research Questions")
    updated_questions = []
    for i, q in enumerate(questions):
        col_q, col_del = st.columns([5, 1])
        with col_q:
            val = st.text_input(
                f"Question {i+1}",
                value=q,
                key=f"rq_{i}",
                placeholder="e.g. What is the impact of climate change on agriculture?"
            )
            updated_questions.append(val)
        with col_del:
            if len(questions) > 1:
                if st.button("✕", key=f"del_rq_{i}", help="Remove this question"):
                    questions.pop(i)
                    st.session_state.research_questions = questions
                    st.rerun()

    st.session_state.research_questions = updated_questions

    col_add, col_research = st.columns([1, 2])
    with col_add:
        if st.button("➕ Add Question", use_container_width=True):
            st.session_state.research_questions.append("")
            st.rerun()
    with col_research:
        if st.button("🔬 Research All Questions", type="primary", use_container_width=True):
            valid_qs = [q.strip() for q in st.session_state.research_questions if q.strip()]
            if not valid_qs:
                st.warning("Please enter at least one question.")
            else:
                with st.spinner(f"🔍 Researching {len(valid_qs)} question(s) independently…"):
                    st.session_state.research_results = run_multi_question_research(valid_qs)
                st.rerun()

    # Display results
    if st.session_state.research_results:
        st.divider()
        st.markdown("### 📋 Research Results")
        st.caption("Each answer is generated independently — no cross-contamination between questions.")

        for i, result in enumerate(st.session_state.research_results):
            with st.expander(f"❓ Q{i+1}: {result['question']}", expanded=(i == 0)):
                st.markdown(result["answer"])
                # Option to open as chatbot context
                if st.button(f"💬 Discuss Q{i+1} in Chatbot", key=f"discuss_{i}"):
                    from memory.memory_store import save_chat_message
                    context_msg = f"I just researched: **{result['question']}**\n\nHere's what was found:\n\n{result['answer']}\n\nCan you help me understand this better?"
                    st.session_state.chat_messages.append({
                        "role": "user",
                        "content": context_msg,
                        "timestamp": datetime.now().strftime("%H:%M"),
                    })
                    save_chat_message("user", context_msg)
                    st.session_state.stage = "chatbot"
                    st.rerun()

        # Download all results
        st.divider()
        results_json = json.dumps(st.session_state.research_results, indent=2, ensure_ascii=False)
        st.download_button(
            label="⬇️ Download Research (JSON)",
            data=results_json,
            file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
        )

        if st.button("🔄 New Research", use_container_width=True):
            st.session_state.research_questions = [""]
            st.session_state.research_results = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PLAN
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "plan":
    st.markdown(f"## 📋 Study Plan: *{st.session_state.topic}*")

    if not st.session_state.plan:
        with st.spinner("🤖 Building your 5-day study plan..."):
            try:
                from agents.planner_agent import run_planner
                st.session_state.plan = run_planner(st.session_state.topic)
            except Exception as e:
                st.error(f"Error generating plan: {e}")
                st.stop()

    plan = st.session_state.plan
    if "error" in plan and plan.get("total_days", 0) == 0:
        st.error(f"Plan generation failed: {plan.get('error')}")
        st.code(plan.get("raw", ""))
    else:
        days = plan.get("days", [])
        cols = st.columns(len(days)) if days else []
        for i, (day, col) in enumerate(zip(days, cols)):
            with col:
                st.markdown(f"**Day {day['day']}**")
                st.markdown(f"*{day['title']}*")
                st.caption(day.get("goal", ""))
                for sub in day.get("subtopics", []):
                    st.markdown(f"• {sub}")
                st.divider()
                if st.button(f"Study Day {day['day']}", key=f"day_{i}", use_container_width=True):
                    subtopics = day.get("subtopics", [])
                    st.session_state.current_subtopic = subtopics[0] if subtopics else day["title"]
                    st.session_state.selected_day = day["day"]
                    st.session_state.notes = ""
                    st.session_state.stage = "research"
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RESEARCH (single-topic, from plan)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "research":
    from agents.researcher_agent import run_researcher
    from memory.memory_store import save_note, add_to_history

    subtopic = st.session_state.current_subtopic or st.session_state.topic
    st.markdown(f"## 📖 Researching: *{subtopic}*")

    if not st.session_state.notes:
        with st.spinner(f"🔍 Researching '{subtopic}'..."):
            try:
                notes = run_researcher(subtopic)
                st.session_state.notes = notes
                save_note(subtopic=subtopic, notes=notes, topic=st.session_state.topic)
                add_to_history("assistant", f"Researched: {subtopic}")
            except Exception as e:
                st.error(f"Research failed: {e}")
                st.stop()

    st.markdown(st.session_state.notes)
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🧠 Take Quiz on This Topic", type="primary", use_container_width=True):
            st.session_state.quiz = {}
            st.session_state.user_answers = {}
            st.session_state.eval_result = {}
            st.session_state.stage = "quiz"
            st.rerun()
    with col2:
        if st.button("📋 Back to Plan", use_container_width=True):
            st.session_state.stage = "plan"
            st.rerun()
    with col3:
        if st.button("💬 Discuss in Chatbot", use_container_width=True):
            from memory.memory_store import save_chat_message
            ctx = f"I just studied **{subtopic}**. Here are my notes:\n\n{st.session_state.notes[:2000]}\n\nCan you help me understand this better or quiz me on it?"
            st.session_state.chat_messages.append({
                "role": "user", "content": ctx,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            save_chat_message("user", ctx)
            st.session_state.stage = "chatbot"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# QUIZ
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "quiz":
    from agents.quiz_agent import run_quiz_generator

    subtopic = st.session_state.current_subtopic or st.session_state.topic
    st.markdown(f"## 🧠 Quiz: *{subtopic}*")

    if not st.session_state.quiz:
        with st.spinner("📝 Generating quiz questions..."):
            try:
                st.session_state.quiz = run_quiz_generator(
                    notes=st.session_state.notes,
                    topic=subtopic,
                )
            except Exception as e:
                st.error(f"Quiz generation failed: {e}")
                st.stop()

    quiz = st.session_state.quiz
    if "error" in quiz and not quiz.get("questions"):
        st.error(f"Quiz failed: {quiz.get('error')}")
        st.code(quiz.get("raw", ""))
    else:
        questions = quiz.get("questions", [])
        if not questions:
            st.warning("No questions generated. Try again.")
        else:
            with st.form("quiz_form"):
                answers = {}
                for q in questions:
                    st.markdown(f"**Q{q['id']}. {q['question']}**")
                    opts = q.get("options", {})
                    choice = st.radio(
                        f"q{q['id']}",
                        options=list(opts.keys()),
                        format_func=lambda k, o=opts: f"{k}. {o[k]}",
                        key=f"q_{q['id']}",
                        label_visibility="collapsed",
                    )
                    answers[q["id"]] = choice
                    st.markdown("")
                if st.form_submit_button("✅ Submit Answers", type="primary", use_container_width=True):
                    st.session_state.user_answers = answers
                    st.session_state.stage = "result"
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RESULT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "result":
    from agents.evaluator_agent import evaluate_answers, get_ai_feedback
    from memory.memory_store import add_to_history

    st.markdown("## 📊 Quiz Results")

    if not st.session_state.eval_result:
        with st.spinner("🤖 Evaluating your answers..."):
            result = evaluate_answers(st.session_state.quiz, st.session_state.user_answers)
            feedback = get_ai_feedback(result)
            st.session_state.eval_result = result
            st.session_state.ai_feedback = feedback
            add_to_history("assistant", f"Score: {result['score_pct']}%")

    result = st.session_state.eval_result
    feedback = st.session_state.ai_feedback

    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{result['score_pct']}%")
    col2.metric("Correct", f"{result['correct']} / {result['total_questions']}")
    col3.metric("Status", "✅ PASSED" if result["passed"] else "🔄 NEEDS REVIEW")

    st.divider()
    st.markdown("### 💬 AI Coach Feedback")
    st.info(feedback)

    st.divider()
    st.markdown("### 📋 Answer Breakdown")
    for f in result.get("feedback", []):
        icon = "✅" if f["is_correct"] else "❌"
        with st.expander(f"{icon} Q{f['id']}: {f['question'][:70]}..."):
            st.markdown(f"**Your answer:** {f['your_answer']}")
            st.markdown(f"**Correct answer:** {f['correct_answer']}")
            if not f["is_correct"]:
                st.markdown(f"**Explanation:** {f['explanation']}")

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if not result["passed"] and st.session_state.retry_count < 2:
            if st.button("🔄 Re-study & Retry", type="primary", use_container_width=True):
                st.session_state.retry_count += 1
                st.session_state.notes = ""
                st.session_state.quiz = {}
                st.session_state.eval_result = {}
                st.session_state.stage = "research"
                st.rerun()
    with col2:
        if st.button("📋 Back to Plan", use_container_width=True):
            st.session_state.stage = "plan"
            st.rerun()
    with col3:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.stage = "home"
            st.rerun()
