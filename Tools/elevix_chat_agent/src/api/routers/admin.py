import os
import shutil
import sys
from typing import List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from src.database import DatabaseManager
from src.api.routers.auth import decode_token
from src.api.schemas import FileInfo

# --- Import RAG Modules ---
# Ensure we can import modules from sibling directories (elevix_rag)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Path to "Tools" directory (parent of elevix_chat_agent and elevix_rag)
tools_dir = os.path.abspath(os.path.join(current_dir, "../../../../"))
rag_dir = os.path.join(tools_dir, "elevix_rag")

if rag_dir not in sys.path:
    sys.path.append(rag_dir)
if tools_dir not in sys.path:
    sys.path.append(tools_dir)

try:
    import ingest
    from elevix_rag.config import Config as RagConfig
    # Also import retriever reload function
    from elevix_rag.retriever import reload_retriever
except ImportError as e:
    print(f"Warning: Could not import RAG modules in admin.py: {e}")
    ingest = None
    RagConfig = None
    reload_retriever = None

router = APIRouter()
db = DatabaseManager()

# Path to dataset (Local to agent)
DATASET_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../dataset"))
if not os.path.exists(DATASET_DIR):
    os.makedirs(DATASET_DIR)

def verify_admin(token: str):
    data = decode_token(token)
    if not data or data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return data

@router.post("/admin/upload")
async def upload_file(file: UploadFile = File(...), token: str = Query(...)):
    verify_admin(token)
    
    file_path = os.path.join(DATASET_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Register in DB
        size = os.path.getsize(file_path)
        db.add_file_record(file.filename, size)
        
        # Trigger Ingestion
        if ingest:
            print(f"Triggering ingestion for {file_path}")
            ingest.ingest_documents(input_path=file_path)
            if reload_retriever:
                print("Reloading retriever...")
                reload_retriever()
        else:
            print("Ingest module not available, skipping vectorization.")
        
        return {"filename": file.filename, "status": "uploaded and processed"}
    except Exception as e:
        print(f"Upload/Ingest Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/files", response_model=List[dict]) 
async def list_files(token: str = Query(...)): # Todo: Use Schema
    verify_admin(token)
    return db.get_all_files()

@router.delete("/admin/files/{filename}")
async def delete_file(filename: str, token: str = Query(...)):
    verify_admin(token)
    
    file_path = os.path.join(DATASET_DIR, filename)
    if os.path.exists(file_path):
        import gc
        import time
        try:
            os.remove(file_path)
        except PermissionError:
            gc.collect()
            time.sleep(0.5)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete {filename}: {e}")
                raise HTTPException(status_code=500, detail="File is in use, try again later.")
    
    db.delete_file_record(filename)
    return {"status": "deleted"}

@router.delete("/admin/reset")
async def reset_system(token: str = Query(...)):
    verify_admin(token)
    # 1. Clear Dataset Files
    import gc
    import time
    
    # helper for safe removal
    def safe_remove(path, retries=3):
        for i in range(retries):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                return
            except PermissionError:
                gc.collect() # Force garbage collection to release handles
                time.sleep(0.5)
                if i == retries - 1:
                    print(f"Failed to delete {path}")

    if os.path.exists(DATASET_DIR):
        for f in os.listdir(DATASET_DIR):
            file_path = os.path.join(DATASET_DIR, f)
            if os.path.isfile(file_path):
                safe_remove(file_path)
    
    # 2. Clear Vector Store
    if RagConfig and hasattr(RagConfig, 'VECTOR_STORE_PATH'):
        vs_path = RagConfig.VECTOR_STORE_PATH
        if os.path.exists(vs_path):
            try:
                shutil.rmtree(vs_path)
                print(f"Vector store at {vs_path} deleted.")
            except Exception as e:
                print(f"Error deleting vector store: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to clear vector store: {e}")
        
        # Reload retriever to reflect empty store
        if reload_retriever:
            reload_retriever()
    
    return {"status": "system reset (files and vectors wiped)"}

@router.delete("/admin/reset-db")
async def reset_db(token: str = Query(...)):
    verify_admin(token)
    db.nuke_db()
    # Re-create admin user
    db.create_user("admin", "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918", "System Admin", "admin") # admin123
    return {"status": "database reset"}

@router.delete("/admin/vectors")
async def clear_vectors(token: str = Query(...)):
    verify_admin(token)
    
    # Clear Vector Store Only
    if RagConfig and hasattr(RagConfig, 'VECTOR_STORE_PATH'):
        vs_path = RagConfig.VECTOR_STORE_PATH
        if os.path.exists(vs_path):
            try:
                shutil.rmtree(vs_path)
                print(f"Vector store at {vs_path} deleted.")
            except Exception as e:
                print(f"Error deleting vector store: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to clear vector store: {e}")

    # Reload retriever
    if reload_retriever:
        reload_retriever()

    return {"status": "vector index cleared"}
