import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import load_config
from app.two_pass_summarizer import TwoPassSummarizer
import json 
import glob

def test_summary():
    config = load_config()
    corpus_dir = Path("data/training_corpus")
    target_files = ["GAS0008.json", "GAS0027.json"]
    json_files = [str(corpus_dir / f) for f in target_files if (corpus_dir / f).exists()]
    
    summarizer = TwoPassSummarizer(config.summarizer)
    
    for idx, json_path in enumerate(json_files):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        case_name = Path(json_path).stem
        transcript = data.get("raw_transcript")
        
        print(f"\n==========================================")
        print(f"SUMMARIZING: {case_name}")
        print(f"==========================================")
        
        summary = summarizer.summarize(transcript)
        print(summary)
        print("\n\n")

if __name__ == "__main__":
    test_summary()
