import os
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import AppConfig, load_config
from app.two_pass_summarizer import TwoPassSummarizer

def main():
    config = load_config()
    from app.hardware import detect_and_configure_gpu
    detect_and_configure_gpu()
    
    # Target Ground Truth transcripts for pure clinical reasoning validation
    truth_dir = Path("data/GiTestValid")
    output_file = Path("GOD_MODE_AUDIT.md")
    
    summarizer = TwoPassSummarizer(config.summarizer)
    
    from app.guideline_rag import GuidelineRAG
    summarizer.rag = GuidelineRAG()
    
    test_cases = ["GAS0001", "GAS0002", "GAS0003", "GAS0004", "GAS0005", "GAS0007"]
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# GI Scribe - God Mode Clinical Reasoning (Full Audit)\n\n")
        f.write("This report contains the raw structured output for each GAS benchmark case.\n")
        f.write("- **Engine**: Two-Pass God-Mode (Llama 3.1 8B Optimized)\n")
        f.write("- **Dual-GPU**: TRX 3060 (Reasoning) + GTX 1650 (Transcription reserved)\n\n")

    for stem in test_cases:
        truth_path = truth_dir / f"{stem}.txt"
        if not truth_path.exists():
             continue
             
        print(f"Auditing results for {stem}...")
        transcript_text = truth_path.read_text(encoding="utf-8")
        
        # Invoke the summarizer
        # We catch the raw structured string by checking internal logs or return
        # Since summarize returns StructuredSummary, we will reconstruct the note
        s_result = summarizer.summarize(transcript_text)
        
        # We reconstruct the full note manually from the result to be safe
        # OR we just grab the 'raw_extraction' which contains the tagged data
        
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"## {stem}\n\n")
            f.write("### HPI NARRATIVE\n")
            f.write(f"{s_result.hpi}\n\n")
            f.write("### EVIDENCE-BASED ASSESSMENT\n")
            for item in s_result.assessment:
                f.write(f"- {item}\n")
            f.write("\n### PLAN & FOLLOWUP\n")
            f.write(f"{s_result.followup}\n")
            f.write("\n---\n\n")
            
        print(f"Processed {stem}.")

if __name__ == "__main__":
    main()
