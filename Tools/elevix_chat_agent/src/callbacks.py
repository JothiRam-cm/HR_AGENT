"""
Custom LangChain callbacks for streaming agent thoughts to UI.
"""
from typing import Any, Dict, List, Optional
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult
import logging
import json

logger = logging.getLogger(__name__)


class StreamingThoughtCallback(BaseCallbackHandler):
    """
    Callback handler that captures agent reasoning steps and makes them available
    for streaming to the UI.
    """
    
    def __init__(self):
        self.thoughts = []
        self.current_step = {}
        
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Called when LLM starts generating."""
        logger.info("🧠 LLM thinking...")
        
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM finishes."""
        logger.info("✓ LLM finished")
        
    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Called when a tool starts executing."""
        tool_name = serialized.get("name", "unknown")
        logger.info(f"⚙️ Tool: {tool_name}")
        logger.info(f"📥 Input: {input_str}")
        
        self.current_step = {
            "type": "tool_start",
            "tool": tool_name,
            "input": input_str,
            "timestamp": self._get_timestamp()
        }
        self.thoughts.append(self.current_step.copy())
        
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool finishes."""
        logger.info(f"📤 Output: {output[:100]}...")
        
        step = {
            "type": "tool_end",
            "output": output[:200] + "..." if len(output) > 200 else output,
            "timestamp": self._get_timestamp()
        }
        self.thoughts.append(step)
        
    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when a tool errors."""
        logger.error(f"❌ Tool error: {error}")
        
        step = {
            "type": "tool_error",
            "error": str(error),
            "timestamp": self._get_timestamp()
        }
        self.thoughts.append(step)
        
    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        """Called when agent decides on an action."""
        logger.info(f"🤔 Thought: {action.log}")
        
        step = {
            "type": "thought",
            "thought": action.log,
            "tool": action.tool,
            "tool_input": str(action.tool_input),
            "timestamp": self._get_timestamp()
        }
        self.thoughts.append(step)
        
    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Called when agent finishes."""
        logger.info(f"✅ Final Answer Ready")
        
        step = {
            "type": "finish",
            "output": finish.return_values.get("output", ""),
            "timestamp": self._get_timestamp()
        }
        self.thoughts.append(step)
        
    def on_text(self, text: str, **kwargs: Any) -> None:
        """Called on arbitrary text."""
        if text.strip():
            logger.debug(f"📝 Text: {text[:100]}")
    
    def get_thoughts(self) -> List[Dict[str, Any]]:
        """Get all captured thoughts."""
        return self.thoughts
    
    def clear(self):
        """Clear captured thoughts."""
        self.thoughts = []
        self.current_step = {}
        
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")


class ThoughtFormatter:
    """Format thoughts for display in UI."""
    
    @staticmethod
    def format_for_display(thoughts: List[Dict[str, Any]]) -> str:
        """
        Format thoughts into human-readable text for UI display.
        
        Returns formatted string with emoji indicators.
        """
        lines = []
        
        for thought in thoughts:
            thought_type = thought.get("type", "")
            timestamp = thought.get("timestamp", "")
            
            if thought_type == "thought":
                tool = thought.get("tool", "unknown")
                lines.append(f"🧠 **Thought** [{timestamp}]")
                lines.append(f"   → Decided to use: `{tool}`")
                
            elif thought_type == "tool_start":
                tool = thought.get("tool", "unknown")
                tool_input = thought.get("input", "")
                lines.append(f"\n⚙️ **Action** [{timestamp}]: `{tool}`")
                lines.append(f"   📥 Input: {tool_input}")
                
            elif thought_type == "tool_end":
                output = thought.get("output", "")
                lines.append(f"   📤 Result: {output}")
                
            elif thought_type == "tool_error":
                error = thought.get("error", "")
                lines.append(f"   ❌ Error: {error}")
                
            elif thought_type == "finish":
                lines.append(f"\n✅ **Final Answer Ready** [{timestamp}]")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_as_json(thoughts: List[Dict[str, Any]]) -> str:
        """Format thoughts as JSON for API transport."""
        return json.dumps(thoughts, indent=2)
