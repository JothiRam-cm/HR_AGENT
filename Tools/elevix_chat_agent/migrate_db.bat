@echo off
echo ========================================
echo   Database Migration Helper
echo ========================================
echo.
echo WARNING: This will DELETE the existing database
echo and recreate it with the new schema.
echo.
echo All existing chat history will be lost!
echo.
pause

echo Deleting old database...
cd /d %~dp0
del chat_history.db 2>nul

echo Database deleted. The new schema will be created
echo automatically when you start the backend.
echo.
echo Run run_app.bat to start the system.
pause
