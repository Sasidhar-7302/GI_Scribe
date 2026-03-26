import multiprocessing
import uvicorn
import webview
import sys
from app.api import app

def run_api():
    uvicorn.run(app, host="127.0.0.1", port=8000)

def main():
    # Start FastAPI in a separate process
    api_process = multiprocessing.Process(target=run_api)
    api_process.start()

    # Wait a bit for server to start
    # In production, we'd bundle the frontend. In dev, we can point to localhost:3000
    # or just open a window to our built index.html
    
    url = "http://localhost:3000" # Development URL
    
    # Create a pywebview window
    window = webview.create_window(
        "GI Scribe - Professional Medical Assistant",
        url,
        width=1400,
        height=900,
        min_size=(1200, 800)
    )
    
    try:
        webview.start()
    finally:
        api_process.terminate()

if __name__ == "__main__":
    main()
