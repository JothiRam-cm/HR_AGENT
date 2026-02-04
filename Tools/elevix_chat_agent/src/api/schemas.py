from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: Optional[str] = None
    user_id: Optional[int] = None

class AdminLogin(BaseModel):
    username: str
    password: str

# --- Chat Schemas ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None

class Citation(BaseModel):
    source: str
    text: Optional[str] = None
    chunk_id: Optional[str] = None
    # For RAG
    page: Optional[int] = None
    file: Optional[str] = None
    location: Optional[str] = None  # Enhanced: Row X, Page Y, Section name, etc.
    # For Web
    url: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    intent: Optional[str] = None
    citations: List[Citation] = []
    conversation_id: Optional[str] = None # Alias for session_id to match frontend expectations
    thoughts: Optional[List[Dict[str, Any]]] = []  # Agent reasoning steps


# --- Admin/File Schemas ---
class FileInfo(BaseModel):
    filename: str
    size_bytes: int
    uploaded_at: str
