import os
from pathlib import Path
from app.config import load_config
from app.transcriber import WhisperTranscriber

def run():
    config = load_config()
    config.whisper.device = "cpu"
    config.whisper.device_index = 0
    config.whisper.compute_type = "int8"
    config.whisper.diarization.enabled = False
    
    t = WhisperTranscriber(config.whisper)
    out_dir = Path("data/gas-txt")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    mp3_paths = []
    for root, _, files in os.walk("local_storage"):
        for f in files:
            if f.endswith(".mp3") and f.startswith("GAS"):
                mp3_paths.append(Path(root) / f)
                
    mp3_paths.sort(key=lambda x: x.name)
    
    seen = set()
    for mp3 in mp3_paths:
        if mp3.name in seen: continue
        seen.add(mp3.name)
        
        print(f"Transcribing {mp3.name} on CPU...")
        try:
            res = t.transcribe(mp3)
            out_file = out_dir / mp3.name.replace(".mp3", ".txt")
            out_file.write_text(res.text, encoding="utf-8")
            print(f"Saved {out_file} ({len(res.text)} chars)")
        except Exception as e:
            print(f"Failed {mp3.name}: {e}")

if __name__ == "__main__":
    run()
