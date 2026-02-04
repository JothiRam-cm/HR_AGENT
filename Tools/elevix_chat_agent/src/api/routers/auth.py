from fastapi import APIRouter, HTTPException, Depends, status
import hashlib
from datetime import datetime, timedelta
import os
import uuid

from src.database import DatabaseManager
from src.api.schemas import UserLogin, UserRegister, Token, AdminLogin

router = APIRouter()
db = DatabaseManager()

# Simple hashing for prototype (In prod, use bcrypt)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Using a simple in-memory token store or just returning ID for this phase
# For real security, use JWT. Here we'll return a "dummy" token that is basically user_id:role
def create_access_token(user_id: int, role: str, full_name: str) -> str:
    # Format: user_id:role:random_uuid
    return f"{user_id}:{role}:{uuid.uuid4()}"

def decode_token(token: str):
    try:
        parts = token.split(":")
        return {"user_id": int(parts[0]), "role": parts[1]}
    except:
        return None

@router.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    existing = db.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = hash_password(user_data.password)
    user = db.create_user(user_data.email, hashed, user_data.full_name)
    
    token = create_access_token(user["id"], user["role"], user["full_name"])
    return Token(access_token=token, token_type="bearer", role=user["role"], full_name=user["full_name"], user_id=user["id"])

@router.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    user = db.get_user_by_email(login_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    hashed = hash_password(login_data.password)
    if hashed != user["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    token = create_access_token(user["id"], user["role"], user["full_name"])
    return Token(access_token=token, token_type="bearer", role=user["role"], full_name=user["full_name"], user_id=user["id"])

@router.post("/admin/login", response_model=Token)
async def admin_login(login_data: AdminLogin):
    # Hardcoded admin check for prototype or check DB
    # If using DB, ensure an admin user is created. 
    # For now, let's allow a hardcoded fallback or DB check.
    
    user = db.get_user_by_email(login_data.username) # Assuming username is email for admin in DB or verify hardcoded
    
    # Fallback Hardcoded Admin
    if login_data.username == "admin" and login_data.password == "admin123":
        # Create a temp admin user in DB if not exists so we have an ID? 
        # Or just return a special token
        return Token(access_token="0:admin:superuser", token_type="bearer", role="admin", full_name="System Admin")

    if user and user["role"] == "admin":
        hashed = hash_password(login_data.password)
        if hashed == user["password_hash"]:
             token = create_access_token(user["id"], user["role"], user["full_name"])
             return Token(access_token=token, token_type="bearer", role="admin", full_name=user["full_name"])

    raise HTTPException(status_code=401, detail="Invalid admin credentials")
