import sys
import os
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# 1. Path Configuration
# ------------------------------------------------------------------------------
# We need to import modules from the sibling directory `elevix_rag`.
# We add it to sys.path so that imports like `from rag_chain import ...` work.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
rag_dir = os.path.join(project_root, "elevix_rag")

if rag_dir not in sys.path:
    sys.path.append(rag_dir)

# ------------------------------------------------------------------------------
# 2. Environment Setup
# ------------------------------------------------------------------------------
# Load environment variables. Priority: Local .env > RAG .env > System env
load_dotenv(os.path.join(current_dir, ".env")) 
load_dotenv(os.path.join(rag_dir, ".env"))

# ------------------------------------------------------------------------------
# 3. Application Logic
# ------------------------------------------------------------------------------
from src.agent import ElevixAgent
from src.adapters import RAGToolAdapter, WebSearchToolAdapter
from llm_factory import get_llm

def main():
    print("==========================================")
    print("       ELEVIX CHAT AGENT (v1.0)           ")
    print("==========================================")
    print("Initializing system components...")
    
    # --- Initialize Tools ---
    try:
        # Defaulting to 'groq' as per project preferences
        provider = "groq"
        rag_tool = RAGToolAdapter(provider=provider)
        print("[OK] HR RAG Tool: Connected")
    except Exception as e:
        print(f"[FAIL] HR RAG Tool: Failed to initialize ({e})")
        print("   -> Tip: Check if 'elevix_rag' is configured and dependencies are installed.")
        return

    try:
        web_tool = WebSearchToolAdapter()
        print("[OK] Web Search Tool: Connected")
    except Exception as e:
        print(f"[FAIL] Web Search Tool: Failed to initialize ({e})")
        return

    # --- Initialize Agent ---
    try:
        llm = get_llm(provider)
        agent = ElevixAgent(rag_tool=rag_tool, web_search_tool=web_tool, llm=llm)
        print("[OK] Elevix Agent: Ready")
    except Exception as e:
        print(f"[FAIL] Elevix Agent: Failed to initialize ({e})")
        return
    
    print("\n------------------------------------------")
    print("Type your message below. Type 'exit' to quit.")
    print("------------------------------------------\n")
    
    # --- Main Loop ---
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nElevix: Goodbye!")
                break
                
            response_data = agent.handle_query(user_input)
            response_text = response_data.get("content", "")
            print(f"\nElevix: {response_text}\n")
            
        except KeyboardInterrupt:
            print("\nElevix: Goodbye!")
            break
        except Exception as e:
            print(f"\n[System Error]: {e}\n")

if __name__ == "__main__":
    main()
