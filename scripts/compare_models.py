import os
import time
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import AppConfig, load_config
from app.transcriber import WhisperTranscriber
import string
import re

def compute_wer(reference, hypothesis):
    # Remove speaker tags
    reference = re.sub(r'^(?:[DP]|Speaker \d+|Doctor|Patient):\s*', '', reference, flags=re.MULTILINE|re.IGNORECASE)
    hypothesis = re.sub(r'^(?:[DP]|Speaker \d+|Doctor|Patient):\s*', '', hypothesis, flags=re.MULTILINE|re.IGNORECASE)
    
    # Strip punctuation
    translator = str.maketrans('', '', string.punctuation)
    reference = reference.translate(translator)
    hypothesis = hypothesis.translate(translator)
    
    r = reference.lower().split()
    h = hypothesis.lower().split()
    
    # Levenshtein distance on words
    d = [[0 for _ in range(len(h) + 1)] for _ in range(len(r) + 1)]
    for i in range(len(r) + 1): d[i][0] = i
    for j in range(len(h) + 1): d[0][j] = j
    
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            cost = 0 if r[i-1] == h[j-1] else 1
            d[i][j] = min(
                d[i-1][j] + 1,      # deletion
                d[i][j-1] + 1,      # insertion
                d[i-1][j-1] + cost  # substitution
            )
    
    errors = d[len(r)][len(h)]
    return (float(errors) / max(len(r), 1)) * 100.0

def evaluate_model(model_path, name):
    print(f"\nEvaluating: {name}")
    config = load_config()
    config.whisper.device = "cuda"
    config.whisper.compute_type = "float16"
    config.whisper.faster_model = model_path
    config.whisper.diarization.enabled = False
    
    transcriber = WhisperTranscriber(config.whisper)
    
    audio_files = ["GAS0008", "GAS0009", "GAS0010"]
    total_wer = 0
    total_time = 0
    count = 0
    
    for case in audio_files:
        audio_path = Path(f"data/GiAudiotest/{case}.mp3")
        json_path = Path(f"data/training_corpus/{case}.json")
        if not audio_path.exists() or not json_path.exists():
            continue
            
        truth_text = json.loads(json_path.read_text(encoding="utf-8")).get("raw_transcript", "")
        t_result = transcriber.transcribe(audio_path)
        wer = compute_wer(truth_text, t_result.text)
        print(f"[{case}] WER: {wer:.2f}%, Time: {t_result.runtime_s:.2f}s")
        total_wer += wer
        total_time += t_result.runtime_s
        count += 1
        
    if count > 0:
        print(f"--- {name} Averages ---")
        print(f"Avg WER: {total_wer/count:.2f}%")
        print(f"Avg Time: {total_time/count:.2f}s")
    else:
        print("No valid files processed.")

if __name__ == '__main__':
    from app.hardware import detect_and_configure_gpu
    detect_and_configure_gpu()
    evaluate_model("large-v3", "General Whisper Large-V3")
    evaluate_model("models/medical-whisper-large-v3-lora-ct2", "Medical Whisper Lora CT2")
