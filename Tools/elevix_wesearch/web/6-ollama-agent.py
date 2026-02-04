import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Reuse existing tools
from tools.get_web_page import get_web_page, get_tool_definition as get_web_page_tool
from tools.search_handbook import search_handbook, get_tool_definition as get_handbook_tool
from tools.get_web_page import get_web_page, get_tool_definition as get_web_page_tool
# We replace the proprietary web_search definition with a standard one
from duckduckgo_search import DDGS

def web_search(query: str) -> str:
    """Perform a web search using DuckDuckGo."""
    try:
        results = DDGS().text(query, max_results=3)
        return json.dumps(results)
    except Exception as e:
        return f"Search Error: {e}"

def get_web_search_tool(allowed_domains: list = None):
    # allowed_domains matching signature of original tool
    return {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the public web for information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"]
            }
        }
    }

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODEL_NAME = "mistral"  # or 'llama3', 'qwen2.5'

SYSTEM_PROMPT = """You are a research assistant.
You have access to tools to search internal handbooks and the public web.
Always use the most appropriate tool.
If you use a tool, cite the source in your final answer."""

def main():
    load_dotenv()
    
    # Connect to Ollama
    client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama" # Required but ignored by Ollama
    )
    
    tools = [
        get_handbook_tool(),
        get_web_page_tool(),
        get_web_search_tool(allowed_domains=["rijksoverheid.nl", "tweedekamer.nl", "cbs.nl"])
    ]
    
    conversation_history = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    print(f"🤖 Ollama Agent ({MODEL_NAME}) Initialized.")
    print("Type 'quit' to exit.\n")

    while True:
        query = input("You: ").strip()
        if query.lower() in ["quit", "exit"]:
            break
            
        conversation_history.append({"role": "user", "content": query})
        
        # 1. Decide on Tool Use
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=conversation_history,
                tools=tools,
                tool_choice="auto"
            )
            
            msg = response.choices[0].message
            tool_calls = msg.tool_calls
            
            # If tools are called
            if tool_calls:
                conversation_history.append(msg) # Add assistant's tool-call message
                
                for tool_call in tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)
                    
                    print(f"🛠️  Calling Tool: {fn_name}")
                    
                    # Execute Tool
                    result = "{}"
                    if fn_name == "search_handbook":
                        result = search_handbook(**fn_args)
                    elif fn_name == "get_web_page":
                        result = get_web_page(**fn_args)
                    elif fn_name == "web_search":
                        result = web_search(**fn_args)
                    
                    conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                
                # 2. Final Synthesis
                final_res = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=conversation_history
                )
                answer = final_res.choices[0].message.content
                print(f"\nAssistant: {answer}\n")
                conversation_history.append({"role": "assistant", "content": answer})
                
            else:
                # No tools used
                answer = msg.content
                print(f"\nAssistant: {answer}\n")
                conversation_history.append({"role": "assistant", "content": answer})

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
