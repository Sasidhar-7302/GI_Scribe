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
    
    transcriber = WhisperTranscriber(config.whisper)
    summarizer = TwoPassSummarizer(config.summarizer)
    
    from app.guideline_rag import GuidelineRAG
    summarizer.rag = GuidelineRAG()
    
    audio_dir = Path("data/GiAudiotest")
    output_file = Path("clinical_benchmark_report.md")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# GI Scribe Clinical Benchmark Report\n\n")
        f.write("System: God-Mode Clinical Reasoner (Dual-GPU Optimized)\n\n")

    test_cases = ["GAS0001", "GAS0002", "GAS0003", "GAS0004", "GAS0005", "GAS0007"]
    
    for stem in test_cases:
        audio_path = audio_dir / f"{stem}.mp3"
        if not audio_path.exists():
             continue
             
        print(f"Bencmarking {stem}...")
        t_start = time.perf_counter()
        t_result = transcriber.transcribe(audio_path)
        s_result = summarizer.summarize(t_result.text)
        total_time = time.perf_counter() - t_start
        
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"## Case {stem}\n")
            f.write(f"- **Total Time**: {total_time:.1f}s\n")
            f.write(f"- **Transcription Time**: {t_result.runtime_s:.1f}s\n")
            f.write(f"- **Summarization Time**: {s_result.runtime_s:.1f}s\n\n")
            f.write("### HPI (History of Present Illness)\n")
            f.write(f"{s_result.hpi}\n\n")
            f.write("### Assessment\n")
            for i, item in enumerate(s_result.assessment):
                f.write(f"{i+1}. {item}\n")
            f.write("\n---\n\n")
            
        print(f"Finished {stem} in {total_time:.1f}s")

if __name__ == "__main__":
    main()
