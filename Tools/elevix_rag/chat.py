import sys
import os

# Ensure the current directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_chain import build_hr_rag_chain

def run_chat():
    print("Welcome to the Strict HR Assistant")
    print("Select Provider: [1] Groq, [2] Gemini, [3] Ollama")
    choice = input("Enter choice (default 1): ").strip()
    
    provider_map = {"1": "groq", "2": "gemini", "3": "ollama"}
    provider = provider_map.get(choice, "groq")
    
    print(f"Initializing with provider: {provider}...")
    try:
        chain = build_hr_rag_chain(provider=provider)
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    chat_history = []
    print("\nHR Assistant is ready. Type 'exit' to stop.\n")

    while True:
        try:
            query = input("You: ")
        except EOFError:
            break
            
        if query.lower() in ["exit", "quit"]:
            break

        if not query.strip():
            continue

        try:
            response = chain.invoke({
                "question": query,
                "chat_history": chat_history
            })
            
            # ConversationalRetrievalChain returns 'answer'
            answer = response.get("answer", "Error: No answer returned.")
            
            print(f"\nHR Bot: {answer}\n")
            
            chat_history.append((query, answer))
        except Exception as e:
            print(f"Error invoking chain: {e}")

if __name__ == "__main__":
    run_chat()
