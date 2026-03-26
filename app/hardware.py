import os
import sys

def detect_and_configure_gpu():
    """
    Dynamically inspects the machine's hardware upon launch.
    Prioritizes the GPU with the highest VRAM. If no GPU is found, 
    it falls back to CPU-only inference, allowing GI Scribe to run anywhere.
    
    This function explicitly mutates `os.environ` to force underlying binaries
    (like faster-whisper and ollama) to respect the detected hardware.
    """
    import torch

    if not torch.cuda.is_available():
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["OLLAMA_VISIBLE_DEVICES"] = ""
        print("[HARDWARE] No CUDA devices detected. Falling back to CPU-only inference.")
        return

    device_count = torch.cuda.device_count()
    best_device_index = 0
    max_memory = 0

    print(f"[HARDWARE] Detected {device_count} CUDA capable device(s).")
    for i in range(device_count):
        props = torch.cuda.get_device_properties(i)
        vram_gb = props.total_memory / (1024**3)
        print(f"  - Device {i}: {props.name} ({vram_gb:.2f} GB VRAM)")
        
        if props.total_memory > max_memory:
            max_memory = props.total_memory
            best_device_index = i

    best_vram_gb = max_memory / (1024**3)
    best_name = torch.cuda.get_device_properties(best_device_index).name
    print(f"\n[HARDWARE] Selected Device {best_device_index}: {best_name} ({best_vram_gb:.2f} GB) as primary AI accelerator.")

    # Pin environmentally so subprocesses (Ollama) respect the choice
    # We only set OLLAMA_VISIBLE_DEVICES here. We do NOT set CUDA_VISIBLE_DEVICES
    # globally if multiple GPUs are present, as that hides the second card from 
    # components like faster-whisper which use our internal device_index config.
    os.environ["OLLAMA_VISIBLE_DEVICES"] = str(best_device_index)
    
    if device_count > 1:
        print(f"[HARDWARE] Multi-GPU environment detected. Ollama pinned to Device {best_device_index}.")
        print(f"[HARDWARE] Other devices remain available for parallel transcription/diarization.")
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(best_device_index)
    
    return best_device_index
