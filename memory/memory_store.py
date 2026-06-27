"""
memory_store.py — Persistent conversation memory + JSON chat log + ChromaDB notes
"""
import os
import json
from datetime import datetime

# ── JSON Chat History (persisted to disk) ─────────────────────────────────────
CHAT_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "chat_history.json")

def _ensure_data_dir():
    os.makedirs(os.path.dirname(CHAT_HISTORY_FILE), exist_ok=True)

def load_chat_history() -> list:
    """Load full chat history from JSON file."""
    _ensure_data_dir()
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[Memory] Failed to load chat history: {e}")
    return []

def save_chat_message(role: str, content: str, metadata: dict = None):
    """Append a single message to the JSON chat history file."""
    _ensure_data_dir()
    history = load_chat_history()
    entry = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    }
    if metadata:
        entry["metadata"] = metadata
    history.append(entry)
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Memory] Failed to save chat message: {e}")

def clear_chat_history():
    """Wipe the JSON chat history file."""
    _ensure_data_dir()
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    except Exception as e:
        print(f"[Memory] Failed to clear chat history: {e}")

def get_chat_history_for_llm(max_turns: int = 20) -> list:
    """Return last N messages in LangChain message format dicts."""
    history = load_chat_history()
    return [{"role": m["role"], "content": m["content"]} for m in history[-max_turns:]]

# ── Session History (in-memory, legacy) ───────────────────────────────────────
_session_history = []
MAX_HISTORY = 50

def add_to_history(role: str, content: str):
    _session_history.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
    if len(_session_history) > MAX_HISTORY:
        _session_history.pop(0)

def get_history():
    return list(_session_history)

def clear_history():
    _session_history.clear()

# ── ChromaDB Study Notes ───────────────────────────────────────────────────────
_collection = None
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")

def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        os.makedirs(CHROMA_DIR, exist_ok=True)
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_or_create_collection("study_notes", metadata={"hnsw:space": "cosine"})
    except Exception as e:
        print(f"[Memory] ChromaDB unavailable: {e}")
        _collection = None
    return _collection

def save_note(subtopic: str, notes: str, topic: str = ""):
    col = _get_collection()
    if col is None:
        return False
    try:
        col.upsert(
            documents=[notes],
            metadatas=[{"subtopic": subtopic, "topic": topic, "saved_at": datetime.now().isoformat()}],
            ids=[f"{topic}::{subtopic}::{datetime.now().isoformat()}"],
        )
        return True
    except Exception as e:
        print(f"[Memory] Save failed: {e}")
        return False

def retrieve_notes(query: str, n_results: int = 3):
    col = _get_collection()
    if col is None or col.count() == 0:
        return []
    try:
        results = col.query(query_texts=[query], n_results=min(n_results, col.count()))
        return [{"content": d, "meta": m} for d, m in zip(results["documents"][0], results["metadatas"][0])]
    except Exception:
        return []

def get_note_count() -> int:
    col = _get_collection()
    try:
        return col.count() if col else 0
    except Exception:
        return 0

def list_all_notes():
    col = _get_collection()
    if col is None:
        return []
    try:
        r = col.get()
        return [{"id": i, "meta": m} for i, m in zip(r["ids"], r["metadatas"])]
    except Exception:
        return []
