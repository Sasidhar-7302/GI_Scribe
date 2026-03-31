@echo off
echo =========================================================
echo                  GI SCRIBE UNIFIED LAUNCHER
echo =========================================================
echo Initializing clean environment...

:: Kill existing processes on ports 3000 and 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul

echo Starting GI Scribe with GPU acceleration (RTX 3060 Pin)...

:: Set Environment
set OLLAMA_VISIBLE_DEVICES=0
set CUDA_VISIBLE_DEVICES=0
set PATH=%~dp0cuda_libs;%PATH%

:: Start Backend in a new window
echo [1/2] Launching Backend AI Engine...
start "GI Scribe Backend" cmd /k "echo GI Scribe Backend (Port 8000) && .\.venv\Scripts\python -m uvicorn app.api:app --host 0.0.0.0 --port 8000"

:: Start Frontend in the current window
echo [2/2] Launching Frontend UI Dashboard...
cd frontend
npm run dev
