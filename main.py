from app.hardware import detect_and_configure_gpu
from app.ui import run

if __name__ == "__main__":
    # 1. Detect and lock hardware resources before UI and PyTorch are initialized.
    best_gpu_index = detect_and_configure_gpu()
    
    # 2. Launch the application
    run()
