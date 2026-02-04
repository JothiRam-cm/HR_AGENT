import os
from typing import Any, List, Optional
from langchain_core.messages import BaseMessage
from langchain_core.language_models import BaseChatModel

# Import providers conditionally to avoid hard crashes if packages missing
try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_community.chat_models import ChatOllama
except ImportError:
    ChatOllama = None

class FallbackAwareLLM:
    """
    A wrapper around multiple LLMs that attempts to invoke them in priority order.
    If the primary fails (e.g. RateLimit), it falls back to the next.
    """
    def __init__(self, llms: List[BaseChatModel]):
        self.llms = llms

    def bind(self, **kwargs: Any) -> Any:
        # Proxy bind to the first LLM. 
        # Note: If the first LLM fails at runtime, the bound parameters might be lost 
        # if the fallback mechanism doesn't re-apply them. 
        # For now, we assume the structure of the agent (e.g. binding stop tokens) 
        # is compatible with the primary LLM.
        # A more robust implementation would need to return a new FallbackAwareLLM 
        # where every internal LLM is bound with these kwargs.
        new_llms = [llm.bind(**kwargs) for llm in self.llms]
        return FallbackAwareLLM(new_llms)

    def invoke(self, messages: Any, **kwargs) -> Any:
        errors = []
        for i, llm in enumerate(self.llms):
            try:
                return llm.invoke(messages, **kwargs)
            except Exception as e:
                print(f"[WARNING] LLM {i} ({type(llm).__name__}) failed: {e}")
                errors.append(str(e))
                if i == len(self.llms) - 1:
                    raise RuntimeError(f"All LLMs failed. Errors: {errors}")

    def __call__(self, messages: Any, **kwargs):
        return self.invoke(messages, **kwargs)

def get_llm_manager(provider: Optional[str] = None, model: Optional[str] = None) -> Any:
    """
    Factory to create the configured LLM or FallbackAwareLLM with automatic fallback to Ollama.
    
    Args:
        provider: Specific provider to use ('groq', 'gemini', 'ollama'). If None, uses env vars.
        model: Specific model name to use. If None, uses defaults or env vars.
    
    Returns:
        BaseChatModel or FallbackAwareLLM with automatic Ollama fallback on errors.
    """
    
    llms = []
    
    # Determine which provider to prioritize based on request
    if provider == "groq":
        # Groq as primary, Ollama as fallback
        groq_key = os.getenv("GROQ_API_KEY")
        groq_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        if groq_key and ChatGroq:
            try:
                llms.append(ChatGroq(api_key=groq_key, model_name=groq_model, temperature=0))
                print(f"[INFO] Initialized Groq with model: {groq_model}")
            except Exception as e:
                print(f"[ERROR] Failed to init Groq: {e}")
                
    elif provider == "gemini":
        # Gemini as primary, Ollama as fallback
        google_key = os.getenv("GOOGLE_API_KEY")
        gemini_model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        if google_key and ChatGoogleGenerativeAI:
            try:
                llms.append(ChatGoogleGenerativeAI(google_api_key=google_key, model=gemini_model, temperature=0))
                print(f"[INFO] Initialized Gemini with model: {gemini_model}")
            except Exception as e:
                print(f"[ERROR] Failed to init Gemini: {e}")
                
    elif provider == "ollama":
        # Ollama requested as primary (no additional fallback needed)
        if ChatOllama:
            ollama_model = model or os.getenv("OLLAMA_MODEL", "mistral")
            ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            try:
                llms.append(ChatOllama(model=ollama_model, base_url=ollama_base, temperature=0))
                print(f"[INFO] Initialized Ollama with model: {ollama_model}")
            except Exception as e:
                print(f"[ERROR] Failed to init Ollama: {e}")
                
    else:
        # No specific provider requested, try all in order from env
        # 1. Setup Groq
        groq_key = os.getenv("GROQ_API_KEY")
        groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        if groq_key and ChatGroq:
            try:
                llms.append(ChatGroq(api_key=groq_key, model_name=groq_model, temperature=0))
                print(f"[INFO] Initialized Groq with model: {groq_model}")
            except Exception as e:
                print(f"[ERROR] Failed to init Groq: {e}")

        # 2. Setup Gemini
        google_key = os.getenv("GOOGLE_API_KEY")
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        if google_key and ChatGoogleGenerativeAI:
            try:
                llms.append(ChatGoogleGenerativeAI(google_api_key=google_key, model=gemini_model, temperature=0))
                print(f"[INFO] Initialized Gemini with model: {gemini_model}")
            except Exception as e:
                print(f"[ERROR] Failed to init Gemini: {e}")
    
    # ALWAYS add Ollama as fallback (unless it's already the primary)
    if provider != "ollama" and ChatOllama:
        ollama_model = os.getenv("OLLAMA_MODEL", "mistral")
        ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            llms.append(ChatOllama(model=ollama_model, base_url=ollama_base, temperature=0))
            print(f"[INFO] Added Ollama fallback with model: {ollama_model}")
        except Exception as e:
            print(f"[WARNING] Could not add Ollama fallback: {e}")

    if not llms:
        raise ValueError("No LLM providers could be initialized. Check .env and installed packages.")

    if len(llms) == 1:
        print(f"[INFO] Using single LLM: {type(llms[0]).__name__}")
        return llms[0]
    
    print(f"[INFO] Using FallbackAwareLLM with {len(llms)} providers")
    return FallbackAwareLLM(llms)

