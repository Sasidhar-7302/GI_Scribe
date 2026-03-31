import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from app.config import load_config
from app.two_pass_summarizer import TwoPassSummarizer

def test_summary_quality():
    config = load_config()
    summarizer = TwoPassSummarizer(config.summarizer)
    
    # Sample transcript with rich history but potentially tricky headers
    sample_transcript = """
SPEAKER_00: Hello Mr. Smith, what brings you in today?
SPEAKER_01: Well doctor, I've had this burning pain in my upper stomach for about two weeks. It's worse after I eat spicy food.
SPEAKER_00: Any nausea or vomiting?
SPEAKER_01: No, just the pain. Maybe a little bloating.
SPEAKER_00: I'm going to start you on Omeprazole 20mg daily and let's see you back in a month.
"""
    
    print("\n[TEST] Running clinical synthesis on sample transcript...")
    # Map speakers first
    mapped = sample_transcript.replace("SPEAKER_00", "Doctor").replace("SPEAKER_01", "Patient")
    
    # Process
    summary = summarizer.summarize_text(mapped)
    
    print("\n" + "="*50)
    print("FINAL CLINICAL NOTE OUTPUT:")
    print("="*50)
    print(summary)
    print("="*50)
    
    # Validation checks
    has_hpi = "HPI (History of Present Illness):" in summary
    has_empty_findings = "Findings:" in summary and "not documented" in summary.lower()
    has_omeprazole = "Omeprazole" in summary
    
    print(f"\n[CHECK] HPI Extracted: {'PASS' if has_hpi and len(summary.split('HPI')[1]) > 20 else 'FAIL'}")
    print(f"[CHECK] Empty Sections Suppressed: {'PASS' if not has_empty_findings else 'FAIL'}")
    print(f"[CHECK] Clinical Facts Preserved: {'PASS' if has_omeprazole else 'FAIL'}")

if __name__ == "__main__":
    test_summary_quality()
