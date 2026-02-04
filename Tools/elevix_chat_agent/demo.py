import os
import sys
from dotenv import load_dotenv

# Add current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent import ElevixAgent
from src.mocks import HRRAGTool, WebSearchTool
from src.llm_manager import get_llm_manager

def main():
    print("Initializing Elevix Chat Agent...")
    
    # Load environment variables from .env_agent
    load_dotenv(".env_agent")
    
    # Instantiate Tools
    rag = HRRAGTool()
    web = WebSearchTool()
    
    # Get LLM (with fallback)
    try:
        llm = get_llm_manager()
        print(f"LLM initialized: {type(llm).__name__}")
    except Exception as e:
        print(f"Critical Error initializing LLM: {e}")
        return

    # Instantiate Agent
    agent = ElevixAgent(rag_tool=rag, web_search_tool=web, llm=llm)
    
    print("\n--- Starting Test Scenarios ---")
    
    scenarios = [
        ("Hello, who are you?", "SMALL_TALK"),
        ("What is the leave policy?", "HR_POLICY"),
        ("What is the weather in Tokyo?", "GENERAL_FACT"),
        ("Tell me a long story about a cat.", "Checking LLM Stream/Response")
    ]
    
    for query, expected_desc in scenarios:
        print(f"\nUser: {query}")
        print(f"Expectation: {expected_desc}")
        try:
            response = agent.handle_query(query)
            print(f"Agent: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
