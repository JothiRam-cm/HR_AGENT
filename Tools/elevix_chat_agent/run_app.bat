@echo off
echo ========================================
echo   ELEVIX System Launcher
echo ========================================
echo.

REM Change to script directory
cd /d %~dp0

REM Kill existing processes
echo [1/3] Cleaning up existing processes...
call kill_ports.bat

REM Start Backend in new window
echo [2/3] Launching Backend API...
start "ELEVIX Backend" cmd /k start_backend.bat

REM Wait for backend to initialize
timeout /t 3 >nul

REM Start Frontend in new window
echo [3/3] Launching Frontend UI...
start "ELEVIX Frontend" cmd /k start_frontend.bat

echo.
echo ========================================
echo   ELEVIX System Started
echo ========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:8501
echo ========================================
echo.
echo Press any key to exit launcher...
pause >nul
