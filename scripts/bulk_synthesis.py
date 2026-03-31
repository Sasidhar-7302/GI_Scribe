import pyttsx3
import re
import os
from pathlib import Path

def synthesize_benchmarks():
    engine = pyttsx3.init()
    engine.setProperty('rate', 155) # Slightly slower for clinical clarity
    engine.setProperty('volume', 1.0)
    
    source_dir = Path("data/Clinical_Encounters")
    txt_files = sorted(list(source_dir.glob("GAS*.txt")))
    
    print(f"Found {len(txt_files)} transcripts to process.")
    
    for txt_path in txt_files:
        mp3_path = txt_path.with_suffix(".mp3")
        print(f"Processing {txt_path.name} -> {mp3_path.name}...")
        
        content = txt_path.read_text(encoding="utf-8")
        
        # Strip D: and P: labels
        # Matches D: or P: at the start of a line, potentially with spaces
        clean_content = re.sub(r'^[DP]:\s*', '', content, flags=re.MULTILINE)
        
        # Also clean up any trailing label remnants if any
        clean_content = clean_content.strip()
        
        try:
            engine.save_to_file(clean_content, str(mp3_path))
            engine.runAndWait()
            print(f"  [SUCCESS] Generated {mp3_path.name}")
        except Exception as e:
            print(f"  [ERROR] Failed {txt_path.name}: {e}")

if __name__ == "__main__":
    synthesize_benchmarks()
