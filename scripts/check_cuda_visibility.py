import torch
import os
from pathlib import Path

def check_cuda():
    print("--- CUDA ENVIRONMENT DIAGNOSTIC ---")
    print(f"CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'Not Set')}")
    print(f"OLLAMA_VISIBLE_DEVICES: {os.environ.get('OLLAMA_VISIBLE_DEVICES', 'Not Set')}")
    
    available = torch.cuda.is_available()
    print(f"torch.cuda.is_available(): {available}")
    
    if available:
        count = torch.cuda.device_count()
        print(f"torch.cuda.device_count(): {count}")
        for i in range(count):
            props = torch.cuda.get_device_properties(i)
            print(f"  - Device {i}: {props.name} ({props.total_memory / (1024**3):.2f} GB)")
    else:
        print("!!! NO GPU DETECTED by torch.cuda. This is likely the cause of the failure.")
        print("Checking if NVIDIA drivers are installed via nvidia-smi...")
        import subprocess
        try:
            res = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            print(res.stdout[:500])
        except Exception as e:
            print(f"nvidia-smi check failed: {e}")

if __name__ == "__main__":
    check_cuda()
