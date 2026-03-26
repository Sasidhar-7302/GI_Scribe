"""
Clinical Acoustic Corrector (CAC)
=================================
A middleware pass that uses Llama 3.1 to perform phonetic correction on raw 
transcriptions specifically targeting medical/GI terminology.
"""

import logging
import requests
from typing import Optional
from .config import SummarizerConfig
from .gi_terms import load_gi_terms

class AcousticCorrector:
    def __init__(self, config: SummarizerConfig):
        self.config = config
        self.logger = logging.getLogger("medrec.corrector")
        self.gi_dict = ", ".join(load_gi_terms()[:100]) # Pass top 100 relevant terms as hint

    def correct(self, transcript: str) -> str:
        """Perform a correction pass on the raw transcript."""
        if not transcript or len(transcript) < 20:
            return transcript

        prompt = f"""You are a medical transcription auditor specializing in Gastroenterology.
Your task is to correct phonetic misspellings in the following raw transcript.
Use the provided GI dictionary to ensure condition and medication names are spelled exactly as they should be.

DICTIONARY HINTS: {self.gi_dict}

INSTRUCTIONS:
1. ONLY fix obvious spelling errors of medical terms (e.g., 'sky ritzy' -> 'Skyrizi', 'egd' -> 'EGD').
2. Do NOT summarize.
3. Keep all conversation segments and speaker markers if present.
4. If a word is ambiguous, leave it as is.
5. Return ONLY the corrected transcript.

RAW TRANSCRIPT:
{transcript}

CORRECTED TRANSCRIPT:"""

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0, # Deterministic correction
                "top_p": 0.9,
                "num_predict": 4096,
            },
        }

        try:
            endpoint = f"{self.config.base_url.rstrip('/')}/api/generate"
            response = requests.post(endpoint, json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
            corrected = data.get("response", "").strip()
            
            if corrected and len(corrected) > len(transcript) * 0.5:
                self.logger.info("Acoustic correction successful.")
                return corrected
            return transcript
        except Exception as e:
            self.logger.error(f"Acoustic correction failed: {e}")
            return transcript
