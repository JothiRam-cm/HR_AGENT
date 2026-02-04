import langchain
import os

print(f"Langchain path: {langchain.__path__}")
try:
    import langchain.memory
    print("langchain.memory imported")
except ImportError as e:
    print(f"Error importing langchain.memory: {e}")

try:
    import langchain_community
    print(f"Langchain Community path: {langchain_community.__path__}")
except ImportError as e:
    print(f"Error importing langchain_community: {e}")
