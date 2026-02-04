@echo off
REM Kill Backend on Port 8000
echo Stopping processes on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %%a 2>nul

REM Kill Streamlit (typically 8501-8510)
echo Stopping Streamlit processes...
for /L %%p in (8501,1,8510) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%p') do taskkill /F /PID %%a 2>nul
)

echo All processes stopped.
timeout /t 2 >nul
