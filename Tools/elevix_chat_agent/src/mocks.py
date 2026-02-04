from typing import List, Dict, Any

class HRRAGTool:
    def run(self, query: str, chat_history: List[Any]) -> Dict[str, Any]:
        """
        Mock implementation of HR RAG Tool.
        Returns dummy answers for known queries, or no context for others.
        """
        query_lower = query.lower()
        if "leave" in query_lower or "policy" in query_lower:
            return {
                "answer": "According to the leave policy, you are entitled to 20 days of annual leave.",
                "has_context": True
            }
        elif "unknown" in query_lower:
             return {
                "answer": "",
                "has_context": False
            }
        else:
            # Default behavior for demo purposes if it looks like an HR query
            return {
                "answer": "The company handbook states that work hours are 9 AM to 5 PM.",
                "has_context": True
            }

class WebSearchTool:
    def run(self, query: str) -> str:
        """
        Mock implementation of Web Search Tool.
        """
        return f"Web Search Result for '{query}': The weather in Tokyo is currently 15°C."
