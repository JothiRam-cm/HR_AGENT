from typing import List, Dict, Any
import logging

try:
    from langchain_community.tools import DuckDuckGoSearchResults
except ImportError:
    DuckDuckGoSearchResults = None

# We assume elevix_rag is in sys.path when this is imported
try:
    from rag_chain import build_hr_rag_chain
except ImportError as e:
    print(f"[DEBUG] Import failed: {e}")
    build_hr_rag_chain = None

class RAGToolAdapter:
    def __init__(self, provider: str = "groq"):
        if build_hr_rag_chain is None:
            raise ImportError("Could not import build_hr_rag_chain. Ensure elevix_rag is in sys.path.")
        
        print(f"Initializing RAG Chain with provider: {provider}...")
        self.chain = build_hr_rag_chain(provider=provider)

    def run(self, query: str, chat_history: List[Any]) -> Dict[str, Any]:
        """
        Executes the RAG chain and returns a structured response.
        Expected return: {"answer": str, "has_context": bool}
        """
        formatted_history = []
        temp_human = None
        for msg in chat_history:
            if msg.type == "human":
                temp_human = msg.content
            elif msg.type == "ai":
                if temp_human:
                    formatted_history.append((temp_human, msg.content))
                    temp_human = None

        try:
            response = self.chain.invoke({
                "question": query,
                "chat_history": formatted_history
            })
            
            answer = response.get("answer", "")
            source_documents = response.get("source_documents", [])
            has_context = len(source_documents) > 0
            
            # Format sources for UI with new metadata structure
            sources = []
            if has_context:
                for doc in source_documents:
                    metadata = doc.metadata
                    
                    # Build source description from new metadata
                    file_name = metadata.get("source_file", metadata.get("source", "Unknown"))
                    file_type = metadata.get("file_type", "unknown")
                    
                    # Determine location based on file type
                    if "row_index" in metadata:
                        location = f"Row {metadata['row_index']}"
                        if "sheet_name" in metadata:
                            location += f" (Sheet: {metadata['sheet_name']})"
                    elif "page_number" in metadata:
                        location = f"Page {metadata['page_number']}"
                    elif "section_heading" in metadata:
                        location = metadata["section_heading"]
                    else:
                        location = metadata.get("section", "N/A")
                    
                    sources.append({
                        "file": file_name,
                        "type": file_type,
                        "location": location,
                        "content": doc.page_content[:200] + "..."  # Snippet
                    })

            if "I don't know" in answer or "I couldn't find" in answer:
                 pass

            return {
                "answer": answer,
                "has_context": has_context,
                "sources": sources
            }
            
        except Exception as e:
            logging.error(f"RAG Tool Error: {e}")
            return {
                "answer": "Error executing RAG tool.",
                "has_context": False,
                "sources": []
            }

class WebSearchToolAdapter:
    def __init__(self):
        """Initialize web search - removed rate limiting to allow immediate searches."""
        self.logger = logging.getLogger(__name__)

    def _fallback_search(self, query: str) -> List[Dict[str, Any]]:
        """Last resort: direct HTTP search when ddgs fails."""
        import requests
        from urllib.parse import quote_plus
        
        try:
            self.logger.info("🔄 Using fallback direct HTTP search...")
            
            # Try DuckDuckGo HTML endpoint
            encoded_query = quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Basic HTML parsing (simplified - just get first few results)
                import re
                
                # Extract titles and URLs using regex (not ideal but works for fallback)
                title_pattern = r'class="result__a" href="([^"]+)">([^<]+)</a>'
                snippet_pattern = r'class="result__snippet">([^<]+)</a>'
                
                titles = re.findall(title_pattern, response.text)
                snippets = re.findall(snippet_pattern, response.text)
                
                results = []
                for i, (url, title) in enumerate(titles[:3]):
                    snippet = snippets[i] if i < len(snippets) else ""
                    results.append({
                        'title': title.strip(),
                        'href': url,
                        'body': snippet.strip()
                    })
                
                if results:
                    self.logger.info(f"✅ Fallback search found {len(results)} results")
                    return results
                    
        except Exception as e:
            self.logger.warning(f"Fallback search failed: {e}")
        
        return []

    def run(self, query: str) -> Dict[str, Any]:
        """
        Execute web search with multiple fallback strategies.
        Returns: {"answer": str, "sources": list}
        """
        import time
        from duckduckgo_search import DDGS
        
        self.logger.info(f"🔍 Web search query: {query}")
        
        # Try multiple search strategies with ddgs
        search_strategies = [
            # Strategy 1: Minimal constraints (most permissive)
            {"max_results": 5},
            # Strategy 2: Different API call
            {"max_results": 3, "timelimit": None},
            # Strategy 3: Just basic + no limits
            {},
        ]
        
        for attempt, strategy in enumerate(search_strategies, 1):
            try:
                self.logger.info(f"Attempt {attempt}/{len(search_strategies)} with ddgs strategy: {strategy}")
                
                results = []
                timeout = 20  # Increased timeout
                
                with DDGS(timeout=timeout) as ddgs:
                    # Remove ALL constraints - just basic search
                    raw_results = ddgs.text(query, **strategy) if strategy else ddgs.text(query)
                    results = list(raw_results)
                
                self.logger.info(f"Raw results count: {len(results)}")
                
                if results:
                    self.logger.info(f"✅ Success! Found {len(results)} results")
                    break
                else:
                    self.logger.warning(f"Attempt {attempt}: Empty results, trying next strategy...")
                    continue
                    
            except Exception as e:
                self.logger.warning(f"Attempt {attempt} error: {type(e).__name__}: {e}")
                if attempt < len(search_strategies):
                    continue
        
        # If ddgs failed completely, try fallback
        if not results:
            self.logger.warning("All ddgs strategies failed, trying fallback...")
            results = self._fallback_search(query)
        
        # Process results
        if results:
            answer_parts = []
            sources = []
            
            for i, res in enumerate(results, 1):
                title = res.get('title', 'No Title')
                href = res.get('href', '#')
                body = res.get('body', res.get('snippet', ''))
                
                self.logger.debug(f"Result {i}: {title[:50]}...")
                
                # Build concise answer
                answer_parts.append(f"{i}. **{title}**: {body}")
                sources.append({
                    "title": title,
                    "url": href,
                    "snippet": body
                })
            
            # Synthesize answer from sources
            answer = "\n\n".join(answer_parts)
            
            return {
                "answer": answer,
                "sources": sources
            }
        
        # All strategies exhausted
        self.logger.error(f"❌ All search strategies (including fallback) returned empty")
        return {
            "answer": "I couldn't find any relevant information. The search service may be temporarily unavailable. Please try again later.",
            "sources": []
        }

