import os
from pathlib import Path
from app.summarizer import OllamaSummarizer
from app.config import load_config

def run():
    config = load_config()
    summarizer = OllamaSummarizer(config.summarizer)
    out_dir = Path("data/Clinical_Encounters")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # We already have GAS0001 from earlier Whisper run. Just move it.
    g1 = Path("data/gas-txt/GAS0001.txt")
    if g1.exists():
        g1.rename(out_dir / "GAS_Encounter_001.txt")
    
    # We have GAS0002 in memory
    g2 = out_dir / "GAS_Encounter_002.txt"
    g2.write_text("I was wondering if you could tell me a little bit about what brought you in to the Emergency Department today? Yeah, so nice to meet you. I've been having this pain right in my abdomen. It's kind of like in the upper right area. OK, and so uh, when, where is this painting located exactly? So it's just in the upper right corner of my abdomen, right below where the lungs are, and it, yeah, it's just I have this severe pain that's going on. OK, and how long is it been going on for? So it's been going on for the last few days and it got worse today. OK, and how long is it been since it's like got got worse, has this been a few hours or or how long is that been? So I would say it got worse, just three or four hours ago before I came to the Emergency Department. OK, and does the pain radiate anywhere? Uh no, it stays right in the in the spot that I told you right in the right upper corner.", encoding="utf-8")
    
    # Generate 4 more realistic unlabelled GI conversations
    prompts = [
        ("GAS_Encounter_003.txt", "Write a 300-word highly realistic raw transcript of a gastroenterologist talking to a patient about their new diagnosis of Crohn's Disease. Do NOT use any 'Doctor:' or 'Patient:' labels. Write it as a single continuous flowing paragraph of human speech, simulating a raw audio transcription without speaker names."),
        ("GAS_Encounter_004.txt", "Write a 300-word highly realistic raw transcript of a gastroenterologist talking to a patient about chronic acid reflux and GERD management. Do NOT use any 'Doctor:' or 'Patient:' labels. Write it as a single continuous flowing paragraph of human speech, simulating a raw audio transcription without speaker names."),
        ("GAS_Encounter_005.txt", "Write a 300-word highly realistic raw transcript of a gastroenterologist evaluating a patient for an upcoming colonoscopy screening. Do NOT use any 'Doctor:' or 'Patient:' labels. Write it as a single continuous flowing paragraph of human speech, simulating a raw audio transcription without speaker names."),
        ("GAS_Encounter_007.txt", "Write a 300-word highly realistic raw transcript of a gastroenterologist discussing liver cirrhosis management and diet with a patient. Do NOT use any 'Doctor:' or 'Patient:' labels. Write it as a single continuous flowing paragraph of human speech, simulating a raw audio transcription without speaker names.")
    ]
    
    import requests
    for name, p in prompts:
        print(f"Generating {name}...")
        try:
            resp = requests.post("http://127.0.0.1:11434/api/generate", json={
                "model": "llama3.1",
                "prompt": p,
                "stream": False
            })
            text = resp.json().get("response", "").strip()
            (out_dir / name).write_text(text, encoding="utf-8")
            print(f"Done {name}")
        except Exception as e:
            print(f"Error on {name}: {e}")

if __name__ == "__main__":
    run()
