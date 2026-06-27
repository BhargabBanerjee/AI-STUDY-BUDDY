# 🎓 AI Study Buddy

An AI-powered personal tutor built with Streamlit. It plans your study schedule, researches topics, generates quizzes, evaluates your answers, and lets you chat with an AI — with support for PDF and image uploads.

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 AI Chatbot | Unlimited multi-turn conversation with full memory |
| 📎 File Upload | Upload PDFs or images — get instant AI summaries |
| 🔬 Multi-Question Research | Research multiple questions independently in one go |
| 📋 5-Day Study Planner | AI generates a structured study plan for any topic |
| 📖 Topic Research | Deep notes on any subtopic with optional web search |
| 🧠 Quiz Generator | Auto-generates 5 MCQs from your study notes |
| 📊 Evaluator + Feedback | Scores your quiz and gives personalized AI coaching |
| 📜 Persistent Chat History | All conversations saved to JSON, searchable, downloadable |
| 🔌 Multi-Provider | Supports Mistral, Gemini, and Ollama |

---

## 🗂️ Project Structure

```
ai_study_buddy_updated/
│
├── app.py                        # Main Streamlit app — all UI pages
│
├── agents/
│   ├── llm_setup.py              # LLM provider switcher (Mistral / Gemini / Ollama)
│   ├── chatbot_agent.py          # Chatbot: multi-turn, PDF, image handling
│   ├── planner_agent.py          # 5-day study plan generator
│   ├── researcher_agent.py       # Topic research + optional Tavily web search
│   ├── quiz_agent.py             # MCQ quiz generator
│   └── evaluator_agent.py        # Answer evaluator + AI feedback
│
├── memory/
│   └── memory_store.py           # JSON chat history + ChromaDB notes storage
│
├── tools/                        # Reserved for future tool integrations
│
├── data/                         # Auto-created at runtime
│   ├── chat_history.json         # Persistent chat log
│   └── chroma_db/                # Vector store for study notes
│
├── .env.example                  # Copy to .env and fill in your API keys
└── requirements.txt              # Python dependencies
```

---

## ⚙️ Setup

### 1. Clone or extract the project

```bash
cd E:\
# Extract the zip or place the folder here
cd ai_study_buddy_updated
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install langchain-mistralai pypdf Pillow
```

> If you're using Gemini instead of Mistral, `pypdf` and `Pillow` are still needed for PDF/image support.

### 4. Configure your API keys

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Then open `.env` and fill in your keys:

```env
# Choose your provider: mistral | gemini | ollama
LLM_PROVIDER=mistral

# Mistral (https://console.mistral.ai)
MISTRAL_API_KEY=your_mistral_api_key_here

# Gemini (https://aistudio.google.com)
GOOGLE_API_KEY=your_google_api_key_here

# Tavily web search — optional (https://app.tavily.com)
TAVILY_API_KEY=your_tavily_api_key_here
```

You only need to fill in the key for the provider you're using.

### 5. Run the app

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 🔌 LLM Providers

### Mistral (Recommended)
- Get a free API key at [console.mistral.ai](https://console.mistral.ai)
- Text model: `mistral-small-latest`
- Image vision model: `pixtral-12b-2409` (used automatically when you upload an image)
- Set `LLM_PROVIDER=mistral` in `.env`

### Gemini
- Get a free API key at [aistudio.google.com](https://aistudio.google.com)
- Model: `gemini-2.0-flash`
- Supports both text and image vision natively
- Set `LLM_PROVIDER=gemini` in `.env`

### Ollama (Local)
- Install Ollama from [ollama.com](https://ollama.com)
- Run `ollama pull mistral` to download the model
- No API key needed — runs fully offline
- Set `LLM_PROVIDER=ollama` in `.env`
- Note: Image vision not supported in Ollama mode

> You can switch providers live from the sidebar dropdown without restarting.

---

## 📖 How to Use

### 💬 Chatbot
1. Click **Chatbot** in the sidebar
2. Type any question in the text box and click **Send**
3. The AI remembers the full conversation — ask follow-up questions freely
4. Optionally attach a **PDF** or **image** using the file uploader
5. The AI will analyze the file and answer your prompt based on its content

### 📎 File Upload (in Chatbot)
| File Type | What happens |
|---|---|
| PDF (`.pdf`) | Text is extracted from all pages and summarized |
| Image (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.bmp`) | Sent to vision model (Pixtral for Mistral, native for Gemini) |

### 🔬 Multi-Question Research
1. Click **Multi-Q Research** in the sidebar
2. Enter one or more research questions
3. Click **➕ Add Question** to add more
4. Click **Research All Questions** — each question is answered independently with a fresh response
5. Download all results as JSON, or click **Discuss in Chatbot** to continue in the chatbot

### 📋 Study Plan
1. Go to **Home**, enter a topic, click **Generate Study Plan**
2. The AI creates a 5-day plan with subtopics and goals
3. Click **Study Day X** to start researching that day's content

### 📖 Research
- Reads a subtopic deeply and generates structured notes
- If `TAVILY_API_KEY` is set, it also pulls in live web results
- After reading, you can take a quiz or discuss the topic in the chatbot

### 🧠 Quiz
- Automatically generates 5 multiple-choice questions based on your notes
- Submit your answers to get a score and detailed AI feedback
- If you score below 60%, you can re-study and retry (up to 2 retries)

### 📜 Chat History
- Every chatbot message is automatically saved to `data/chat_history.json`
- View full history from the sidebar → **View Full History**
- Search/filter messages, expand to read in full
- Download the entire history as a JSON file anytime
- Clear history with the **🗑️ Clear Chat** button in the sidebar

---

## 🛠️ Troubleshooting

### `cannot import name 'ChatMistralAI' from 'langchain_community'`
The class moved to a dedicated package. Fix:
```bash
.venv\Scripts\pip install langchain-mistralai
```
Then make sure `agents/llm_setup.py` uses:
```python
from langchain_mistralai import ChatMistralAI
```

### `pypdf not found` when uploading a PDF
```bash
.venv\Scripts\pip install pypdf
```

### `Pillow not found` when uploading an image
```bash
.venv\Scripts\pip install Pillow
```

### ChromaDB errors on startup
```bash
.venv\Scripts\pip install chromadb --upgrade
```

### Tavily search not working
Make sure `TAVILY_API_KEY` is set in your `.env`. If you don't have a key, web search is simply skipped — the app still works without it.

### Switching providers mid-session
Use the **🔌 LLM Provider** dropdown in the sidebar. The change takes effect on the next message/action.

---

## 📦 Dependencies

```
langchain-mistralai       # Mistral LLM integration
langchain-community       # Shared LangChain utilities
langchain-google-genai    # Gemini LLM integration
langchain-core            # LangChain base classes
langgraph                 # Agent graph orchestration
chromadb                  # Vector store for study notes
tavily-python             # Optional web search
streamlit                 # Web UI framework
python-dotenv             # .env file loader
pypdf                     # PDF text extraction
Pillow                    # Image processing
```

---

## 🔐 API Keys Summary

| Key | Where to get it | Required? |
|---|---|---|
| `MISTRAL_API_KEY` | [console.mistral.ai](https://console.mistral.ai) | If using Mistral |
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | If using Gemini |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) | Optional (web search) |

---

## 📄 License

This project is for personal and educational use. Feel free to modify and extend it.# AI-STUDY-BUDDY
# AI-STUDY-BUDDY
