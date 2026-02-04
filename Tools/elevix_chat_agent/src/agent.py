import logging
import os
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain.tools import Tool

from src.intents import classify_intent, INTENT_HR_POLICY, INTENT_GENERAL_FACT, INTENT_SMALL_TALK
from src.memory_manager import MemoryManager

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are Ray, a conversational HR assistant.

Behavior Rules:
- Be polite, professional, and clear.
- Engage naturally in conversation.
- You have access to tools, but you must follow strict rules:

CRITICAL CITATION REQUIREMENT:
- For ANY substantive query (not greetings/small talk), you MUST use a tool and provide sources.
- NEVER answer factual or policy questions from memory alone.
- If a user asks a real question, you MUST cite sources.

Strict Rules:
- HR or Leave related questions MUST use the hr_policy_tool.
- HR questions MUST NEVER use web search.
- If hr_policy_tool reports insufficient context, respond with:
  "I couldn't find this information in the company documents."
- General factual questions MUST use web_search_tool and cite the sources.
- Casual conversation (greetings, thanks) should NOT use any tool.
- Never hallucinate policies or rules.
- Always acknowledge the sources you used in your final answer.

TOOLS:
------

Ray has access to the following tools:

{tools}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response for the user, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

Begin!

Chat History:
{chat_history}

Question: {input}
Thought:{agent_scratchpad}
"""

class ElevixAgent:
    def __init__(self, rag_tool_adapter: Any, web_search_tool_adapter: Any, llm: Any, memory_manager: MemoryManager):
        self.rag_adapter = rag_tool_adapter
        self.web_adapter = web_search_tool_adapter
        self.llm = llm
        self.memory_manager = memory_manager
        
        pass


    def _run_web_search(self, query: str) -> str:
        logger.info(f"Calling Web Search Tool with query: {query}")
        result = self.web_adapter.run(query=query)
        if isinstance(result, dict):
            return result.get("answer", "")
        return str(result)


    def handle_query(self, user_query: str, session_id: str) -> Dict[str, Any]:
        logger.info(f"Processing query for session {session_id}: {user_query}")
        
        # 1. Load context and memory
        memory_obj = self.memory_manager.get_memory(session_id)
        chat_history = memory_obj.chat_memory.messages
        chat_history_str = memory_obj.load_memory_variables({}).get("chat_history", "")
        
        # 2. Intent Classification
        intent = classify_intent(user_query, chat_history=str(chat_history_str), llm=self.llm)
        logger.info(f"Detected Intent: {intent}")

        # 3. Define Tools with dynamic context and source capture
        captured_sources = []

        def run_hr_tool(q):
            logger.info(f"Agent calling hr_policy_tool with: {q}")
            result = self.rag_adapter.run(query=q, chat_history=chat_history)
            if result.get("sources"):
                captured_sources.extend(result["sources"])
            return result.get("answer", "I couldn't find this information.")

        def run_web_tool(q):
            logger.info(f"Agent calling web_search_tool with: {q}")
            result = self.web_adapter.run(query=q)
            if isinstance(result, dict) and result.get("sources"):
                captured_sources.extend(result["sources"])
                return result.get("answer", "")
            return str(result)

        tools = [
            Tool(
                name="hr_policy_tool",
                func=run_hr_tool,
                description="Useful for questions about HR policies, leave, holidays, and company rules."
            ),
            Tool(
                name="web_search_tool",
                func=run_web_tool,
                description="Useful for general factual questions NOT related to HR or company policies."
            )
        ]

        # 4. Create callback to capture thoughts
        from src.callbacks import StreamingThoughtCallback
        thought_callback = StreamingThoughtCallback()

        # 5. Execute via AgentExecutor
        prompt = PromptTemplate.from_template(SYSTEM_PROMPT)
        agent = create_react_agent(self.llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory_obj,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15,
            early_stopping_method="generate",
            callbacks=[thought_callback]  # Add callback here
        )
        
        try:
            input_text = f"[Intent: {intent}] {user_query}"
            response = agent_executor.invoke({"input": input_text})
            answer = response.get("output", "")
            
            # Get captured thoughts
            thoughts = thought_callback.get_thoughts()
            
            # 6. Store in SQLite
            self.memory_manager.save_message(session_id, "user", user_query)
            self.memory_manager.save_message(session_id, "assistant", answer, {
                "intent": intent, 
                "sources": captured_sources,
                "thoughts": thoughts  # Store thoughts in metadata
            })
            
            return {
                "content": answer,
                "intent": intent,
                "session_id": session_id,
                "sources": captured_sources,
                "thoughts": thoughts  # Return thoughts for UI
            }
        except Exception as e:
            logger.error(f"Error in agent execution: {e}")
            return {
                "content": f"I apologize, but I encountered an error: {str(e)}",
                "intent": intent,
                "session_id": session_id,
                "sources": [],
                "thoughts": []
            }

