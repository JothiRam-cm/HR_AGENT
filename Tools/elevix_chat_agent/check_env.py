import sys
import os

print(f"Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print("Path:")
for p in sys.path:
    print(p)

try:
    import langchain
    print(f"LangChain version: {langchain.__version__}")
    from langchain.memory import ConversationBufferMemory
    print("ConversationBufferMemory imported successfully")
except ImportError as e:
    print(f"ImportError: {e}")

try:
    import langchain_openai
    print("langchain_openai found")
except ImportError:
    print("langchain_openai NOT found")
