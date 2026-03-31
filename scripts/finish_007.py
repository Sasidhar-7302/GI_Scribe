import pyttsx3
from pathlib import Path

def finish():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    base_dir = Path("data/Clinical_Encounters")
    
    tid = "007"
    txt_path = base_dir / f"GAS_Encounter_{tid}.txt"
    mp3_path = base_dir / f"GAS_Encounter_{tid}.mp3"
    
    if txt_path.exists():
        print(f"Generating {tid}...")
        text = txt_path.read_text(encoding="utf-8")
        engine.save_to_file(text, str(mp3_path))
        engine.runAndWait()
        print(f"Done {tid}")

if __name__ == "__main__":
    finish()
