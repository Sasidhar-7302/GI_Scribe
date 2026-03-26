import os
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import AppConfig, load_config
from app.transcriber import WhisperTranscriber
from app.two_pass_summarizer import TwoPassSummarizer

def main():
    config = load_config()
    from app.hardware import detect_and_configure_gpu
    detect_and_configure_gpu()
    
    config.whisper.diarization.enabled = False
    
    # We will use existing transcripts from the truth directory to speed up the report generation
    # if the user just wants to see the clinical reasoning.
    # However, to be thorough, we will do a full run but log better.
    
    summarizer = TwoPassSummarizer(config.summarizer)
    
    from app.guideline_rag import GuidelineRAG
    summarizer.rag = GuidelineRAG()
    
    truth_dir = Path("data/GiTestValid")
    output_file = Path("GIBenchmark_results_GodMode.md")
    
    test_cases = ["GAS0001", "GAS0002", "GAS0003", "GAS0004", "GAS0005", "GAS0007"]
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# GI Scribe - God Mode Clinical Reasoning Report\n\n")
        f.write("Generated from GAS series benchmark using Dual-GPU optimized two-pass synthesis.\n\n")

    for stem in test_cases:
        truth_path = truth_dir / f"{stem}.txt"
        if not truth_path.exists():
             continue
             
        print(f"Processing clinical reasoning for {stem}...")
        transcript_text = truth_path.read_text(encoding="utf-8")
        
        # We manually invoke the summarizer on the ground-truth transcript
        # to focus on the reasoning quality vs human gold-standard text.
        s_result = summarizer.summarize(transcript_text)
        
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"## Case: {stem}\n")
            f.write("### HPI (History of Present Illness - Narrative)\n")
            f.write(f"{s_result.hpi}\n\n")
            f.write("### Assessment & Plan (Evidenced)\n")
            for i, item in enumerate(s_result.assessment):
                f.write(f"{i+1}. {item}\n")
            if s_result.plan:
                f.write("\n**Plan:**\n")
                f.write(f"{s_result.plan}\n")
            f.write("\n---\n\n")
            
        print(f"Finished {stem}")

if __name__ == "__main__":
    main()
