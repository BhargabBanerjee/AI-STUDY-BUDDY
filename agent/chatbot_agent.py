import os
import base64
import mimetypes
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agents.llm_setup import get_llm

SYSTEM_PROMPT = """You are an intelligent AI Study Buddy — a helpful, knowledgeable assistant.
You can answer any question, help with research, explain concepts, analyze uploaded files, and summarize content.
When given files (PDFs, images), provide a clear and thorough summary/analysis.
Always give fresh, thoughtful answers based on the actual question asked — do not repeat previous answers verbatim.
Be concise yet complete. Use markdown formatting for clarity."""


def run_chatbot(
    user_message: str,
    conversation_history: list,
    uploaded_file_bytes: bytes = None,
    uploaded_file_name: str = None,
    uploaded_file_type: str = None,
) -> str:
    llm = get_llm(temperature=0.7)
    provider = os.getenv("LLM_PROVIDER", "mistral").lower()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in conversation_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    if uploaded_file_bytes and uploaded_file_name:
        mime = uploaded_file_type or mimetypes.guess_type(uploaded_file_name)[0] or "application/octet-stream"
        ext = (uploaded_file_name.rsplit(".", 1)[-1]).lower() if "." in uploaded_file_name else ""

        if ext == "pdf":
            return _handle_pdf(llm, user_message, uploaded_file_bytes, uploaded_file_name)
        elif ext in ("png", "jpg", "jpeg", "gif", "webp", "bmp"):
            return _handle_image(llm, user_message, uploaded_file_bytes, mime, provider, messages)
        else:
            try:
                text_content = uploaded_file_bytes.decode("utf-8", errors="replace")
                prompt = f"{user_message}\n\n[File: {uploaded_file_name}]\n{text_content[:5000]}"
            except Exception:
                prompt = f"{user_message}\n\n[File attached: {uploaded_file_name} — could not read content]"
            messages.append(HumanMessage(content=prompt))
    else:
        messages.append(HumanMessage(content=user_message))

    response = llm.invoke(messages)
    return response.content.strip()


def _handle_pdf(llm, user_message, file_bytes, file_name):
    try:
        import io
        text = ""
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            except ImportError:
                return "❌ PDF reading requires pypdf. Install with: pip install pypdf"

        if not text.strip():
            text = "[PDF appears to be scanned/image-based — no extractable text found]"

        prompt = f"""{user_message}

[PDF File: {file_name}]
Content:
{text[:8000]}
{"...[truncated]" if len(text) > 8000 else ""}

Please provide a thorough summary and answer the user's prompt with respect to this document."""

        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        return response.content.strip()
    except Exception as e:
        return f"❌ Error processing PDF: {e}"


def _handle_image(llm, user_message, file_bytes, mime_type, provider, prior_messages):
    try:
        b64 = base64.b64encode(file_bytes).decode("utf-8")

        if provider == "mistral":
            from langchain_mistralai import ChatMistralAI
            vision_llm = ChatMistralAI(
                model="pixtral-12b-2409",
                api_key=os.getenv("MISTRAL_API_KEY"),
                temperature=0.4,
            )
            content = [
                {"type": "text", "text": f"{user_message}\n\nPlease analyze this image thoroughly."},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
            ]
            msgs = [SystemMessage(content=SYSTEM_PROMPT)]
            for m in prior_messages[1:]:
                if hasattr(m, "content") and isinstance(m.content, str):
                    msgs.append(m)
            msgs.append(HumanMessage(content=content))
            response = vision_llm.invoke(msgs)
            return response.content.strip()

        elif provider == "gemini":
            content = [
                {"type": "text", "text": f"{user_message}\n\nPlease analyze this image thoroughly."},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
            ]
            prior_messages.append(HumanMessage(content=content))
            response = llm.invoke(prior_messages)
            return response.content.strip()

        else:
            prior_messages.append(HumanMessage(content=f"{user_message}\n\n[Image uploaded — switch to Mistral or Gemini for vision support]"))
            response = llm.invoke(prior_messages)
            return response.content.strip()

    except Exception as e:
        return f"❌ Error processing image: {e}"


def run_multi_question_research(questions: list[str]) -> list[dict]:
    results = []
    llm = get_llm(temperature=0.7)

    research_system = """You are a research assistant. For each question, provide a comprehensive,
fresh, and unique answer based solely on the question itself.
Format your answer with clear sections using markdown."""

    for q in questions:
        try:
            response = llm.invoke([
                SystemMessage(content=research_system),
                HumanMessage(content=f"Research and answer this question thoroughly: {q}")
            ])
            results.append({"question": q, "answer": response.content.strip()})
        except Exception as e:
            results.append({"question": q, "answer": f"❌ Error: {e}"})

    return results