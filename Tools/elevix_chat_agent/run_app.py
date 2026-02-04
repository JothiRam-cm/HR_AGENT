import subprocess
import time
import os
import sys

def run_app():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Use venv python explicitly
    venv_python = os.path.join(os.path.dirname(script_dir), ".venv", "Scripts", "python.exe")
    
    # 1. Start Backend
    print("Starting Uvicorn Backend...")
    backend_process = subprocess.Popen(
        [venv_python, "src/api/main.py"],
        cwd=script_dir
    )
    
    # Wait for backend to be potentially ready
    time.sleep(5)
    
    # 2. Start Frontend
    print("Starting Streamlit Frontend...")
    frontend_process = subprocess.Popen(
        [venv_python, "-m", "streamlit", "run", "streamlit_app.py"],
        cwd=script_dir
    )
    
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    run_app()
