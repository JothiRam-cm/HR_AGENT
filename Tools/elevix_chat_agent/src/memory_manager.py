import logging
from typing import List, Any
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage
from src.database import DatabaseManager

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, db_manager: DatabaseManager, window_size: int = 5):
        self.db_manager = db_manager
        self.window_size = window_size

    def get_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """
        Creates and rehydrates memory for a given session.
        """
        logger.info(f"Rehydrating memory for session: {session_id}")
        
        # Initialize memory with the key we want (default is 'history' but some agents expect 'chat_history')
        # AgentExecutor with individual tools often uses 'chat_history'
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=self.window_size
        )

        # Load history from SQLite
        history_messages = self.db_manager.get_messages(session_id, limit=self.window_size * 2)
        
        for msg in history_messages:
            if msg["role"] == "user":
                memory.chat_memory.add_message(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                memory.chat_memory.add_message(AIMessage(content=msg["content"]))
        
        return memory

    def save_message(self, session_id: str, role: str, content: str, metadata: Any = None):
        """
        Saves a message to the SQLite database.
        """
        self.db_manager.add_message(session_id, role, content, metadata)
