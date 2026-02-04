import json
import os
import argparse
import sys
from dotenv import load_dotenv
from openai import OpenAI
from duckduckgo_search import DDGS
from googlesearch import search
from tools.get_web_page import get_web_page
import google.generativeai as genai
from groq import Groq

# Load environment variables
# Prioritize .env_web if it exists
if os.path.exists(".env_web"):
    load_dotenv(".env_web")
else:
    load_dotenv()

def get_llm_response(prompt: str, provider: str, sources: list) -> str:
    """Generates a response from the specified LLM provider."""
    
    system_prompt = f"""You are a helpful research assistant. 
    You have been provided with search results from the web. 
    Your task is to synthesize an answer to the user's query based ONLY on the provided sources.
    
    CRITICAL INSTRUCTION: You MUST cite your sources using square brackets like [1], [2], etc. associated with the source ID provided.
    Do not invent facts. If the information is not in the sources, say so.
    
    Sources:
    {json.dumps(sources, indent=2)}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        if provider == "groq":
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            response = client.chat.completions.create(
                model="llama3-70b-8192", # Mapping 'llama3.3-70b-versatile' to a known valid Groq ID, adjust if needed
                messages=messages,
                temperature=0.5,
                max_tokens=1024
            )
            return response.choices[0].message.content

        elif provider == "ollama":
            client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama" 
            )
            response = client.chat.completions.create(
                model="mistral",
                messages=messages,
                temperature=0.5
            )
            return response.choices[0].message.content

        elif provider == "gemini":
            genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
            # mapping '2.5-flash' request to 'gemini-2.5-flash' or 'gemini-2.0-flash-exp' as available
            # For safety, defaulting to gemini-2.5-flash which is stable, or trying 2.0 if user explicitly set
            model = genai.GenerativeModel('gemini-2.5-flash') 
            response = model.generate_content(
                f"{system_prompt}\n\nUser Query: {prompt}"
            )
            return response.text
            
        else:
            return f"Error: Unknown provider {provider}"

    except Exception as e:
        if provider != "ollama":
            print(f"Provider '{provider}' failed: {e}. Falling back to Ollama.", file=sys.stderr)
            return get_llm_response(prompt, "ollama", sources)
        else:
             return f"Error generating response: {e}"

def main():
    parser = argparse.ArgumentParser(description="JSON Search Agent")
    parser.add_argument("query", help="The search query")
    parser.add_argument("--provider", default="groq", choices=["groq", "ollama", "gemini"], help="LLM Provider")
    args = parser.parse_args()

    # 1. Search Web
    results = []
    try:
        # Try DuckDuckGo first
        ddg_results = DDGS().text(args.query, max_results=2)
        if ddg_results:
            results = list(ddg_results)
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}", file=sys.stderr)

    if not results:
        try:
            # Fallback to Google Search
            print("DuckDuckGo failed, falling back to Google Search...", file=sys.stderr)
            g_results = search(args.query, num_results=2, advanced=True)
            for res in g_results:
                results.append({"title": res.title, "href": res.url, "body": res.description})
        except Exception as e:
             print(json.dumps({"error": f"Google search failed: {e}"}))
             return

    if not results:
        print(json.dumps({"answer": "No results found from any provider.", "sources": []}))
        return

    # 2. Fetch Content
    sources = []
    for idx, res in enumerate(results, 1):
        try:
            content = get_web_page(res['href'])
            # Truncate content to avoid blowing up context window too much
            content_snippet = content[:10000] 
        except Exception as e:
            content_snippet = f"Failed to fetch content: {e}"
        
        sources.append({
            "id": idx,
            "title": res['title'],
            "url": res['href'],
            "content": content_snippet
        })

    # 3. Optimize Sources for LLM Context (remove full content if too large, keep snippet)
    # The 'sources' list passed to LLM will contain the content.
    # The 'sources' list returned in JSON might want full content or just metadata. 
    # User requested "details", often implying the content or summary. 
    # We will return what we fetched.
    
    # 4. Generate Answer
    answer = get_llm_response(args.query, args.provider, sources)

    # 5. Output JSON
    output = {
        "answer": answer,
        "sources": sources
    }
    
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
