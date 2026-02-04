from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
import uuid
import logging

from src.database import DatabaseManager
from src.api.routers.auth import decode_token
from src.api.schemas import ChatRequest, ChatResponse, Citation
from src.agent import ElevixAgent

# Logic for agent/tools/llm initialization from existing codebase
from src.llm_manager import get_llm_manager
from src.adapters import RAGToolAdapter, WebSearchToolAdapter
from src.memory_manager import MemoryManager

router = APIRouter()
logger = logging.getLogger("elevix_backend")
db = DatabaseManager()
memory_manager = MemoryManager(db)

# Agent components (reusable)
_rag_adapter = None
_web_adapter = None

def get_agent(provider: str = "groq", model: str = "llama-3.3-70b-versatile"):
    """
    Create an agent instance with specified provider and model.
    Reuses RAG and web adapters for efficiency.
    """
    global _rag_adapter, _web_adapter
    
    try:
        # Initialize adapters once (they don't depend on LLM model)
        if _rag_adapter is None:
            _rag_adapter = RAGToolAdapter()
            logger.info("Initialized RAG adapter")
            
        if _web_adapter is None:
            _web_adapter = WebSearchToolAdapter()
            logger.info("Initialized Web adapter")
        
        # Create LLM with requested provider/model (includes automatic Ollama fallback)
        llm = get_llm_manager(provider=provider, model=model)
        
        # Create new agent instance
        agent_instance = ElevixAgent(
            rag_tool_adapter=_rag_adapter,
            web_search_tool_adapter=_web_adapter,
            llm=llm,
            memory_manager=memory_manager
        )
        
        logger.info(f"Created agent with provider={provider}, model={model}")
        return agent_instance
        
    except Exception as e:
        logger.error(f"Failed to init agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent initialization failed: {str(e)}")

def get_current_user_id(authorization: str = Header(None)):
    if not authorization:
        return None # Anonymous permitted for demo, or raise 401
    
    try:
        token = authorization.replace("Bearer ", "")
        data = decode_token(token)
        if data:
            return data["user_id"]
    except:
        pass
    return None

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, user_id: Optional[int] = Depends(get_current_user_id)):
    # Get provider and model from request or use defaults
    provider = request.provider or "groq"
    model = request.model or "llama-3.3-70b-versatile"
    
    # Create agent with specified provider/model (includes Ollama fallback)
    agent = get_agent(provider=provider, model=model)
    
    # Session Management
    session_id = request.session_id or str(uuid.uuid4())
    
    # Save user message to DB first (handled by memory manager effectively, but we want to ensure session link)
    # The agent.handle_query calls memory_manager.save_message, which calls db.add_message.
    # We should update db.create_session_if_not_exists to link user_id if present.
    db.create_session_if_not_exists(session_id, user_id)
    
    try:
        logger.info(f"Processing chat for user {user_id}, session {session_id}")
        response_data = agent.handle_query(request.message, session_id)
        
        # Parse Sources into Citations
        citations = []
        raw_sources = response_data.get("sources", [])
        
        for src in raw_sources:
            if "file" in src:
                # Build location string from new metadata
                location = None
                if "row_index" in src:
                    location = f"Row {src['row_index']}"
                    if "sheet_name" in src:
                        location += f" (Sheet: {src['sheet_name']})"
                elif "page_number" in src:
                    location = f"Page {src['page_number']}"
                elif "section_heading" in src:
                    location = src["section_heading"]
                else:
                    location = src.get("section", "N/A")
                
                citations.append(Citation(
                    source=f"Document: {src.get('file')}",
                    text=src.get('content'),
                    file=src.get('file'),
                    page=src.get('page'),
                    location=location
                ))
            elif "url" in src:
                citations.append(Citation(
                    source=src.get('url'),
                    text=src.get('snippet'), # Use snippet as text
                    url=src.get('url'),
                    title=src.get('title'),
                    snippet=src.get('snippet')
                ))
            else:
                 # Fallback
                 citations.append(Citation(source="Unknown", text=str(src)))

        return ChatResponse(
            answer=response_data["content"],
            session_id=session_id,
            conversation_id=session_id,
            intent=response_data.get("intent", "UNKNOWN"),
            citations=citations,
            thoughts=response_data.get("thoughts", [])  # Include agent thoughts
        )
        
    except Exception as e:
        logger.error(f"Chat Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/chats") 
async def get_user_chats(user_id: int = Depends(get_current_user_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    sessions = db.get_user_sessions(user_id)
    
    # Format for UI
    # We might want full history or just list. `get_user_sessions` returns list with preview.
    # The frontend expects a list of conversations with messages? Or just metadata?
    # Based on app.py: "for chat in history_data.get('conversations', []):"
    
    # Let's populate the full messages for the UI logic to reduce calls
    results = []
    for s in sessions:
        msgs = db.get_messages(s["session_id"], limit=100)
        formatted_msgs = []
        for m in msgs:
            # Map DB role to UI role if needed
            role = m["role"]
            content = m["content"]
            
            # Map to structure app.py expects: {user: "...", assistant: "...", citations: []}
            # Actually app.py loop suggests simple mapping or pair mapping.
            # Let's verify app.py logic... 
            # app.py: for msg in chat.get('messages', []): if msg.get('user'): ...
            # The current app.py `api_user_chat` returns simple answer. `api_get_user_history` handles history.
            
            # We'll stick to a simple list of messages for now and let Frontend Adapter parse it, 
            # OR we match app.py expectations. 
            # app.py parse logic:
            # loaded_messages.append({"role": "user", "content": msg['user']})
            # loaded_messages.append({"role": "assistant", "content": msg['assistant']})
            
            # Since our DB stores individual messages, we need to group them or change Frontend.
            # Changing Frontend is part of the plan. We will return a standard list of messages here.
            
            formatted_msgs.append({
                "role": role,
                "content": content,
                "citations": [] # Citations stored in metadata, need to extract?
            })
            
        results.append({
            "conversation_id": s["session_id"],
            "messages": formatted_msgs # Frontend will need to adapt to this "flat" list vs "pairs"
        })
        
    return {"conversations": results}

@router.get("/history/{session_id}")
async def get_history(session_id: str):
    msgs = db.get_messages(session_id)
    return {"session_id": session_id, "history": msgs}
