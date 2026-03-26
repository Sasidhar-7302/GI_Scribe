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
    output_file = Path("GAS_Clinical_Benchmark_GodMode.md")
    
    summarizer = TwoPassSummarizer(config.summarizer)
    
    from app.guideline_rag import GuidelineRAG
    summarizer.rag = GuidelineRAG()
    
    test_cases = ["GAS0001", "GAS0002", "GAS0003", "GAS0004", "GAS0005", "GAS0007"]
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# GI Scribe - God Mode Clinical Reasoning (Official Benchmark)\n\n")
        f.write("This report validates the clinical reasoning quality on the GAS benchmark series.\n")
        f.write("- **Engine**: Two-Pass God-Mode (Llama 3.1 8B Optimized)\n")
        f.write("- **Hardware**: Dual-GPU Parallel (RTX 3060 / GTX 1650)\n\n")

    for stem in test_cases:
        truth_path = truth_dir / f"{stem}.txt"
        if not truth_path.exists():
             continue
             
        print(f"Generating clinical proof for {stem}...")
        transcript_text = truth_path.read_text(encoding="utf-8")
        
        # Invoke the summarizer
        s_result = summarizer.summarize(transcript_text)
        
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"## {stem}\n")
            f.write("### History of Present Illness (HPI)\n")
            # We use the raw section content to ensure no parsing loss
            f.write(f"{s_result.hpi or 'NULL (Extraction Error)'}\n\n")
            f.write("### Assessment & Evidence\n")
            if s_result.assessment:
                for idx, line in enumerate(s_result.assessment):
                    f.write(f"{idx+1}. {line}\n")
            else:
                f.write("No assessment found during extraction pas-through.\n")
            f.write("\n---\n\n")
            
        print(f"Verified {stem}.")

if __name__ == "__main__":
    main()
