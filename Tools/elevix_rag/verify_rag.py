
import sys
import os

# Ensure the current directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_chain import build_hr_rag_chain

def test_rag():
    print("Testing RAG Chain...")
    try:
        # Try with ollama as it is free and local, or groq if user set it up. 
        # User said they added keys, so I will try 'groq' first as it is default.
        # If it fails, I'll catch it.
        provider = "groq" 
        print(f"Initializing with provider: {provider}...")
        chain = build_hr_rag_chain(provider=provider)
        
        query = "What is the policy on sick leave?"
        print(f"Query: {query}")
        
        response = chain.invoke({
            "question": query,
            "chat_history": []
        })
        
        answer = response.get("answer", "No answer")
        print(f"Answer: {answer}")
        print("RAG Verification: SUCCESS")
        
    except Exception as e:
        print(f"RAG Verification FAILED: {e}")

if __name__ == "__main__":
    test_rag()
