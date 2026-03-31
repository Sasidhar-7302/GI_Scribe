import pyttsx3
import os
from pathlib import Path

def generate_audio():
    # Setup paths
    base_dir = Path("data/Clinical_Encounters")
    if not base_dir.exists():
        print(f"Directory {base_dir} not found.")
        return

    # Initialize TTS engine
    engine = pyttsx3.init()
    
    # Configure voice properties (Slow down for medical clarity)
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 0.9)
    
    # List of files to process (Skip 001 as it's already there as mp3)
    target_ids = ["002", "003", "004", "005", "007"]
    
    for tid in target_ids:
        txt_file = base_dir / f"GAS_Encounter_{tid}.txt"
        mp3_file = base_dir / f"GAS_Encounter_{tid}.mp3"
        
        if txt_file.exists():
            print(f"Synthesizing {mp3_file}...")
            text = txt_file.read_text(encoding="utf-8")
            
            # pyttsx3 save_to_file
            # Note: On Windows, pyttsx3 might only support .wav natively through Sapi5, 
            # but let's try .mp3 first. If it fails, use .wav.
            try:
                engine.save_to_file(text, str(mp3_file))
                engine.runAndWait()
                print(f"Successfully generated {mp3_file}")
            except Exception as e:
                print(f"Failed to generate {mp3_file}: {e}")
        else:
            print(f"Transcript {txt_file} not found.")

if __name__ == "__main__":
    generate_audio()
