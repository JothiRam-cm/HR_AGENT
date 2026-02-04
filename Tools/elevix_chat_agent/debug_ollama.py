try:
    from langchain_community.chat_models import ChatOllama
    print("ChatOllama imported from langchain_community.chat_models")
except ImportError as e:
    print(f"Failed from chat_models: {e}")

try:
    from langchain_community.chat_models.ollama import ChatOllama
    print("ChatOllama imported from langchain_community.chat_models.ollama")
except ImportError as e:
    print(f"Failed from chat_models.ollama: {e}")
