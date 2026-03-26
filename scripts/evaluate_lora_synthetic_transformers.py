import os
import glob
import json
import time
import sys
import torch
import librosa
from pathlib import Path
from transformers import WhisperForConditionalGeneration, WhisperProcessor

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.evaluate_accuracy import compute_wer

def evaluate_lora():
    model_id = "models/medical-whisper-lora-merged"
    print(f"[*] Loading native PyTorch transformers LoRA model: {model_id}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load model and processor natively
    processor = WhisperProcessor.from_pretrained(model_id)
    model = WhisperForConditionalGeneration.from_pretrained(model_id, torch_dtype=torch.float16).to(device)
    
    corpus_dir = Path("data/training_corpus")
    target_files = ["GAS0008.json", "GAS0027.json"]
    json_files = [str(corpus_dir / f) for f in target_files if (corpus_dir / f).exists()]
    
    average_wer = 0
    total_files = len(json_files)
    
    for idx, json_path in enumerate(json_files):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        audio_file = data.get("audio_file")
        ground_truth_transcript = data.get("raw_transcript")
        
        if not audio_file or not ground_truth_transcript:
            continue
            
        case_name = Path(audio_file).stem
        print(f"\n--- Testing Synthetic Case: {case_name} ({idx+1}/{total_files}) ---")
        
        start_t = time.time()
        
        # Inference
        from transformers import pipeline
        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            chunk_length_s=30,
            batch_size=1,
            return_timestamps=False,
            device=device
        )
        
        predicted_text = pipe(audio_file)["text"]
        
        end_t = time.time()
        
        wer = compute_wer(ground_truth_transcript, predicted_text)
        average_wer += wer
        
        print(f"Transcription WER: {wer:.2f}% (Lower is better)")
        print(f"Transcription Time: {end_t - start_t:.2f}s")
        
    print(f"\n======================================")
    print(f"OVERALL AVERAGE LORA WER: {average_wer / max(1, total_files):.2f}%")
    print(f"======================================")

if __name__ == "__main__":
    evaluate_lora()
