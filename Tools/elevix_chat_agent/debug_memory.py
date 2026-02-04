
import sys
import os
sys.path.append(os.getcwd())

try:
    from src.database import DatabaseManager
    from src.memory_manager import MemoryManager
    from langchain.schema import HumanMessage, AIMessage
    
    print("Imports successful")
    
    # Test DB
    db = DatabaseManager(":memory:")
    print("DB initialized")
    
    # Test Memory Manager initialization
    memory_manager = MemoryManager(db)
    print("MemoryManager initialized")
    
    session_id = "test_123"
    
    # Test Save
    memory_manager.save_message(session_id, "user", "Hello")
    memory_manager.save_message(session_id, "assistant", "Hi")
    print("Messages saved")
    
    # Test Load
    msgs = db.get_messages(session_id)
    print(f"Messages in DB: {len(msgs)}")
    
    memory = memory_manager.get_memory(session_id)
    chat_hist = memory.chat_memory.messages
    print(f"Messages in memory object: {len(chat_hist)}")
    
    print("SUCCESS")

except Exception as e:
    import traceback
    traceback.print_exc()
