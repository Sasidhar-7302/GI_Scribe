import os
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import AppConfig, load_config
from app.transcriber import WhisperTranscriber
from app.two_pass_summarizer import TwoPassSummarizer

def compute_wer(reference, hypothesis):
    # Simple Word Error Rate
    r = reference.lower().split()
    h = hypothesis.lower().split()
    
    # Levenshtein distance on words
    d = [[0 for _ in range(len(h) + 1)] for _ in range(len(r) + 1)]
    for i in range(len(r) + 1): d[i][0] = i
    for j in range(len(h) + 1): d[0][j] = j
    
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i-1] == h[j-1]:
                cost = 0
            else:
                cost = 1
            d[i][j] = min(
                d[i-1][j] + 1,      # deletion
                d[i][j-1] + 1,      # insertion
                d[i-1][j-1] + cost  # substitution
            )
    
    errors = d[len(r)][len(h)]
    return (float(errors) / max(len(r), 1)) * 100.0

def main():
    config = load_config()
    
    # Force GPU targeting for the test if not set
    config.whisper.device_index = 0
    config.whisper.device = "cuda"
    config.whisper.beam_size = 5
    config.whisper.compute_type = "int8"
    config.whisper.diarization.enabled = False
    config.whisper.faster_model = "large-v3"
    
    transcriber = WhisperTranscriber(config.whisper)
    summarizer = TwoPassSummarizer(config.summarizer)
    summarizer.rag = None  # Disable RAG internet download
    
    audio_dir = Path("data/GiAudiotest")
    truth_dir = Path("data/GiTestValid")
    
    if not audio_dir.exists() or not truth_dir.exists():
        print("Test directories not found.")
        return
        
    audio_files = list(audio_dir.glob("*.mp3"))
    if not audio_files:
        print("No audio files found.")
        return
        
    print(f"Found {len(audio_files)} test files. Beginning accuracy evaluation...")
    
    total_wer = 0.0
    count = 0
    
    for audio_path in audio_files:
        stem = audio_path.stem
        truth_path = truth_dir / f"{stem}.txt"
        
        if not truth_path.exists():
            continue
            
        print(f"\n--- Processing {stem} ---")
        truth_text = truth_path.read_text(encoding="utf-8")
        
        # 1. Transcription Accuracy
        t_result = transcriber.transcribe(audio_path)
        wer = compute_wer(truth_text, t_result.text)
        print(f"Transcription WER: {wer:.2f}% (Lower is better)")
        print(f"Transcription Time: {t_result.runtime_s:.2f}s")
        
        total_wer += wer
        count += 1
        
        # 2. Summarization Quality
        s_result = summarizer.summarize(t_result.text)
        print(f"Summarization Time: {s_result.runtime_s:.2f}s")
        print("\n--- Summary Structure ---")
        print(f"HPI Length: {len(s_result.hpi)} chars")
        print(f"Findings: {len(s_result.findings)} items")
        print(f"Assessment: {len(s_result.assessment)} items")
        print(f"Plan: {len(s_result.plan)} items")
        print("------------------------\n")
        
    if count > 0:
        print(f"=== OVERALL AVERAGE WER: {(total_wer / count):.2f}% ===")

if __name__ == "__main__":
    main()
