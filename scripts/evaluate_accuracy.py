import os
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import AppConfig, load_config
from app.transcriber import WhisperTranscriber
from app.two_pass_summarizer import TwoPassSummarizer

import string
import re
import logging

# Configure logging to see internal steps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

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

def main():
    config = load_config()
    from app.hardware import detect_and_configure_gpu
    detect_and_configure_gpu()
    
    # Ensure it targets the best GPU if available (override CPU fallback if possible)
    if not config.whisper.device or config.whisper.device == "cpu":
        config.whisper.device = "cuda"
        config.whisper.compute_type = "float16" # fallback to f16 if int8 fails

    config.whisper.diarization.enabled = False
    
    print("[DEBUG] Initializing WhisperTranscriber...")
    transcriber = WhisperTranscriber(config.whisper)
    print("[DEBUG] Initializing TwoPassSummarizer...")
    summarizer = TwoPassSummarizer(config.summarizer)
    
    # Initialize RAG for evaluation
    print("[DEBUG] Initializing RAG...")
    from app.guideline_rag import GuidelineRAG
    summarizer.rag = GuidelineRAG()
    print("[DEBUG] RAG initialized.")
    
    audio_dir = Path("data/GiAudiotest")
    truth_dir = Path("data/GiTestValid")
    
    if not audio_dir.exists() or not truth_dir.exists():
        print("Test directories not found.")
        return
        
    audio_files = [audio_dir / f"{f}.mp3" for f in ["GAS0001", "GAS0002", "GAS0003", "GAS0004", "GAS0005", "GAS0007"]]
    audio_files = [f for f in audio_files if f.exists()]
    
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
        
        # 2. Summarization Quality (Enabled for God-Mode verification)
        s_result = summarizer.summarize(t_result.text)
        print(f"Summarization Time: {s_result.runtime_s:.2f}s")
        print("\n--- Summary Content ---")
        print(f"HPI (History of Present Illness):\n{s_result.hpi}")
        print("\nAssessment:")
        for i, item in enumerate(s_result.assessment):
            print(f"{i+1}. {item}")
        print("------------------------\n")
        
    if count > 0:
        print(f"=== OVERALL AVERAGE WER: {(total_wer / count):.2f}% ===")

if __name__ == "__main__":
    main()
