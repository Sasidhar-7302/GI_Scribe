@echo off
echo Safe Cleaning GI Scribe ports 3000 and 8000...
echo [NOTE: This script will NO LONGER close your browser tabs.]

:: Kill node processes on 3000 (Frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo [SAFE] Clearing Frontend port 3000 (PID %%a)...
    taskkill /F /PID %%a 2>nul
)

:: Kill python processes on 8000 (Backend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo [SAFE] Clearing Backend port 8000 (PID %%a)...
    taskkill /F /PID %%a 2>nul
)

echo Safe port cleanup complete.
exit /b 0
