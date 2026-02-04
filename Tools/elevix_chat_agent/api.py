import os
import uuid
import logging
import sys
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# 1. Path Configuration
# ------------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
rag_dir = os.path.join(project_root, "elevix_rag")

if rag_dir not in sys.path:
    sys.path.append(rag_dir)

# Load environment variables
load_dotenv(os.path.join(current_dir, ".env"))
load_dotenv(os.path.join(rag_dir, ".env"))

# ------------------------------------------------------------------------------
# 2. Imports from src
# ------------------------------------------------------------------------------
from src.database import DatabaseManager
from src.memory_manager import MemoryManager
from src.agent import ElevixAgent
from src.adapters import RAGToolAdapter, WebSearchToolAdapter
from src.llm_manager import get_llm_manager

# ------------------------------------------------------------------------------
# 3. Setup Logging
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("agent_backend.log")
    ]
)
logger = logging.getLogger("elevix_backend")

# ------------------------------------------------------------------------------
# 4. FastAPI Setup
# ------------------------------------------------------------------------------
app = FastAPI(title="ELEVIX HR Agent API", version="1.0.0")

# Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    intent: str
    sources: Optional[List[Dict[str, Any]]] = None

# Global state
db_manager = DatabaseManager()
memory_manager = MemoryManager(db_manager)
agent: Optional[ElevixAgent] = None

@app.on_event("startup")
async def startup_event():
    global agent
    logger.info("Starting up ELEVIX Agent Backend...")
    try:
        provider = os.getenv("PRIMARY_PROVIDER", "groq")
        llm = get_llm_manager()
        
        rag_adapter = RAGToolAdapter(provider=provider)
        web_adapter = WebSearchToolAdapter()
        
        agent = ElevixAgent(
            rag_tool_adapter=rag_adapter,
            web_search_tool_adapter=web_adapter,
            llm=llm,
            memory_manager=memory_manager
        )
        logger.info("[OK] Elevix Agent initialized and ready.")
    except Exception as e:
        logger.error(f"[FAIL] Initialization failed: {e}")
        # In a real app, we might want to exit here
        pass

@app.get("/")
async def root():
    return {"status": "online", "message": "ELEVIX HR Agent Backend is running."}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    # Generate session_id if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        logger.info(f"Received message for session {session_id}: {request.message}")
        
        # Process query
        response_data = agent.handle_query(request.message, session_id)
        
        return ChatResponse(
            answer=response_data["content"],
            session_id=session_id,
            intent=response_data.get("intent", "UNKNOWN"),
            sources=response_data.get("sources", [])
        )
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    try:
        messages = db_manager.get_messages(session_id)
        return {"session_id": session_id, "history": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
