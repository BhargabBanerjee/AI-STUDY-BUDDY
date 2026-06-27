import os
from dotenv import load_dotenv
load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mistral").lower()

def get_llm(temperature=0.2):
    if LLM_PROVIDER == "mistral":
        from langchain_mistralai import ChatMistralAI
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise EnvironmentError("MISTRAL_API_KEY not set in .env")
        return ChatMistralAI(model="mistral-small-latest", api_key=api_key, temperature=temperature)
    elif LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY not set in .env")
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key, temperature=temperature)
    elif LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model="mistral", temperature=temperature)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER='{LLM_PROVIDER}'. Choose: mistral | gemini | ollama")