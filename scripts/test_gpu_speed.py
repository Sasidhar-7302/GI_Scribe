import time
import os
from faster_whisper import WhisperModel

# Use a tiny sample of random audio or a file if it exists
def run_benchmark():
    audio_file = "data/gi_data/gas0005.wav"
    if not os.path.exists(audio_file):
        print("Need a valid audio file to test.")
        return

    print("Benchmarking RTX 3060 (Device 0)")
    model0 = WhisperModel("large-v3", device="cuda", device_index=0, compute_type="int8", download_root="models/faster-whisper")
    start = time.perf_counter()
    segs, info = model0.transcribe(audio_file, beam_size=1)
    for s in segs: pass
    t0 = time.perf_counter() - start
    print(f"RTX 3060 Time: {t0:.2f} seconds")
    del model0

    print("Benchmarking GTX 1650 (Device 1)")
    try:
        model1 = WhisperModel("large-v3", device="cuda", device_index=1, compute_type="int8", download_root="models/faster-whisper")
        start = time.perf_counter()
        segs, info = model1.transcribe(audio_file, beam_size=1)
        for s in segs: pass
        t1 = time.perf_counter() - start
        print(f"GTX 1650 Time: {t1:.2f} seconds")
    except Exception as e:
        print(f"GTX 1650 Failed (probably OOM): {e}")

if __name__ == "__main__":
    run_benchmark()
