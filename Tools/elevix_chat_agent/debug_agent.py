
import sys
import os
sys.path.append(os.getcwd())

try:
    from src.agent import ElevixAgent
    from unittest.mock import Mock
    
    print("Import successful")
    
    mock_rag = Mock()
    mock_web = Mock()
    mock_llm = Mock()
    mock_mem = Mock()
    
    agent = ElevixAgent(mock_rag, mock_web, mock_llm, mock_mem)
    print("Instantiation successful")
    
    agent.handle_query("test", "session_1")
    print("Handle query successful")

except Exception as e:
    import traceback
    traceback.print_exc()
