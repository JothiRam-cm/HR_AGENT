from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
# Note: Newer versions might use langchain_ollama, but keeping compatibility or using community if that's what's installed.
# Actually I put langchain-ollama in requirements, so I should use:
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama

from config import Config

def get_llm(provider: str, model_name: str = None):
    if provider == "groq":
        if not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        return ChatGroq(
            model=model_name or Config.MODEL_GROQ,
            temperature=0,
            api_key=Config.GROQ_API_KEY
        )

    if provider == "gemini":
        if not Config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        return ChatGoogleGenerativeAI(
            model=model_name or "gemini-2.5-flash", 
            temperature=0,
            google_api_key=Config.GOOGLE_API_KEY
        )

    if provider == "ollama":
        return ChatOllama(
            model=model_name or Config.MODEL_OLLAMA,
            temperature=0
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")
