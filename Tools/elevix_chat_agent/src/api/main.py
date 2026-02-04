import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
# src/api -> src -> elevix_chat_agent
project_root = os.path.abspath(os.path.join(current_dir, "../..")) 
rag_dir = os.path.join(os.path.dirname(project_root), "elevix_rag") # elevix_rag is sibling to elevix_chat_agent

if rag_dir not in sys.path:
    sys.path.append(rag_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Load Env
load_dotenv(os.path.join(project_root, ".env")) # Root env
load_dotenv(os.path.join(project_root, "elevix_chat_agent/.env")) # Agent env

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("elevix_backend")

# Imports from Routers
from src.api.routers import auth, admin, chat

app = FastAPI(title="Ray Intelligent Agent API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(chat.router)

@app.get("/")
async def root():
    return {"status": "online", "message": "Ray System Operational"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
