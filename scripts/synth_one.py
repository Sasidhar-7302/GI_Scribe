import pyttsx3
import re
from pathlib import Path

def synthesize_one(tid: str):
    engine = pyttsx3.init()
    engine.setProperty('rate', 155)
    
    source_dir = Path("data/Clinical_Encounters")
    txt_path = source_dir / f"GAS{tid}.txt"
    mp3_path = source_dir / f"GAS{tid}.mp3"
    
    if not txt_path.exists():
        print(f"Skipping {tid}: File not found")
        return
        
    print(f"Synthesizing {tid}...")
    content = txt_path.read_text(encoding="utf-8")
    clean_content = re.sub(r'^[DP]:\s*', '', content, flags=re.MULTILINE)
    clean_content = clean_content.strip()
    
    engine.save_to_file(clean_content, str(mp3_path))
    engine.runAndWait()
    print(f"Done {tid}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        synthesize_one(sys.argv[1])
