@echo off
echo Starting GI Scribe with GPU acceleration (RTX 3060 Pin)...
set OLLAMA_VISIBLE_DEVICES=0
set CUDA_VISIBLE_DEVICES=0
set PATH=%~dp0cuda_libs;%PATH%
.\.venv\Scripts\python main.py
