"""
Two-Pass Summarization Engine
==============================
Pass 1: Extract key clinical information from transcript
Pass 2: Structure into proper clinical note format

This improves accuracy by separating understanding from formatting.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Optional, Dict, List

import requests

from .config import SummarizerConfig
from .gi_terms import build_gi_hint
from .gi_post_processor import process_summary
from .prompt_templates import FEW_SHOT_EXAMPLES
try:
    from .guideline_rag import GuidelineRAG
    HAS_RAG = True
except ImportError:
    HAS_RAG = False

from .database import DatabaseManager


@dataclass
class StructuredSummary:
    """Structured clinical summary with all required sections."""
    hpi: str
    findings: List[str]
    assessment: List[str]
    plan: List[str]
    medications: List[str]
    followup: str
    raw_extraction: str
    runtime_s: float
    model_used: str


EXTRACTION_PROMPT = """### Instruction:
You are a Senior Clinical Informaticist and Medical Scribe. Your task is to extract every clinical relevant fact from the transcript below for an EHR update.

**CLINICAL RULES**:
1. **Holistic Review of Systems (ROS)**: You MUST extract symptoms from ALL mentioned systems, not just GI. (e.g., GYN: missed periods; GU: urinary frequency; Constitutional: weight loss, thirst).
2. **Medical Translation**: Convert patient lay-terms to professional terminology (e.g. "throwing up" -> "emesis", "peeing a lot" -> "polyuria/frequency").
3. **Diagnostic Clues**: Note triggers, timing (morning vs evening), and specific descriptors.

**OUTPUT SCHEMA:**
[CHIEF COMPLAINT]: Primary reason.
[TIMELINE]: Detailed progression (e.g., "9 days of constant nausea").
[ROS - PERTINENT POSITIVES]: List every symptom reported as present.
[ROS - PERTINENT NEGATIVES]: List symptoms explicitly denied (fever, blood, etc).
[MEDS/ALLERGIES]: Ginger, birth control history, nickel allergy.
[SOCIAL/PAST]: Roommate, BF, no smoking, rare EtOH.

### Transcript:
{transcript}

### Extracted Clinical Facts:
"""


# Template style to guide the model without providing copyable content
TEMPLATE_STYLE = """
HPI (History of Present Illness):
(Write a paragraph summarizing the history)

Findings:
- (List findings. If none, write "Not documented")
- (Physical exam findings. If none, omit)
- (Lab/Imaging results. If none, omit)

Assessment:
1. (Primary diagnosis)
2. (Secondary diagnoses if any)

Plan:
- (Medications)
- (Tests/Procedures)
- (Referrals)

Medications:
- (List medications. Omit dose/freq if not known)

Orders:
- (List procedures/labs ordered. If none, write "None")

Follow-up:
- (Timing. If none, write "Not documented")
"""

STRUCTURING_PROMPT = """### Instruction:
You are a Board-Certified Gastroenterologist. Structure the extracted facts into a formal, diagnostic clinical note.

**STRICT FORMATTING RULES:**
1. **HPI (History of Present Illness)**: Write a professional narrative paragraph (5-10 sentences). 
   - Combine the timeline, triggers (smells, morning), and all associated symptoms. 
   - **MANDATORY**: Mention the patient's menstrual status (LMP 6 weeks ago) and urinary frequency as they are clinically significant for the differential diagnosis.
2. **Assessment**: Provide a prioritized, numbered problem list. Group related symptoms into syndromes where appropriate (e.g., Morning Nausea and Amenorrhea).
3. **Plan**: Outline the recommended next steps (e.g., "Exclude pregnancy," "Hydration").
4. **Tone**: Use high-level medical prose (e.g., "The patient reports a 9-day history of persistent nausea and occasional emesis...").

{few_shot_examples}

### Extracted Facts:
{extracted_info}

### Clinical Note Output (Start with HPI):
"""


SELF_CORRECTION_PROMPT = """[INST] <<SYS>>
You are a medical quality assurance specialist. Your task is to review a generated clinical note against the original transcript.
Your Goal: Ensure every finding in the note is supported by the transcript, but DO NOT delete valid symptoms (like nausea, missed periods, or pain) reported by the patient.

**CRITICAL RULES:**
1. **RETAIN SYMPTOMS**: If the patient says they have a symptom, it MUST stay in the HPI and Assessment.
2. **STRICT DELETION**: ONLY delete physical exam findings, lab results, or definitive diagnoses (e.g., "Crohn's Disease") IF they are not mentioned by the doctor or patient.
3. **NO REPETITION**: Do not output the same sentence for every section.
4. **FORMAT**: Output ONLY the full clinical note. No meta-commentary.
<</SYS>>

### Original Transcript:
{transcript}

### Generated Note (Review this):
{generated_note}

### Corrected Note (Output ONLY the full note starting with HPI):
[/INST]
HPI (History of Present Illness):"""

# Stage 0: Diarization prompt
DIARIZATION_PROMPT = """### Instruction:
Format the following raw medical transcript as a dialogue between "Doctor:" and "Patient:". 
Do NOT summarize. Keep every word.

### Transcript:
{transcript}

### Dialogue:
Doctor: """

class TwoPassSummarizer:
    """Two-pass summarizer for higher accuracy clinical notes."""

    def __init__(self, config: SummarizerConfig):
        self.config = config
        self.logger = logging.getLogger("medrec.two_pass_summarizer")
        self.max_retries = 2
        self.gi_hints = f"GI Terminology: {build_gi_hint(max_terms=40)}"
        self.rag = GuidelineRAG() if HAS_RAG else None
        self.db = DatabaseManager("medrec.db")

    @property
    def _endpoint(self) -> str:
        return f"{self.config.base_url.rstrip('/')}/api/generate"

    def summarize(self, transcript: str, style: Optional[str] = None) -> StructuredSummary:
        """Generate summary using four-stage approach for maximum accuracy."""
        if not transcript or not transcript.strip():
            raise ValueError("Transcript cannot be empty")

        start_time = time.perf_counter()

        # Stage 0: Diarization (Labeling speakers)
        self.logger.info("two_pass_summarizer | stage=0 | action=diarization")
        diarized_transcript = self.diarize(transcript)

        # Stage 1: Clinical Extraction (Pass 1)
        self.logger.info("two_pass_summarizer | stage=1 | action=extraction")
        extraction_prompt = EXTRACTION_PROMPT.format(
            gi_hints=self.gi_hints,
            transcript=diarized_transcript.strip()
        )
        extracted = self._invoke_model(extraction_prompt, temperature=0.05)
        self.logger.info(f"--- EXTRACTED TEXT PREVIEW ---\n{extracted[:500]}...\n-------------------------------")

        # Stage 1.5: RAG Retrieval
        guidelines_text = ""
        if self.rag:
            self.logger.info("two_pass_summarizer | stage=1.5 | action=rag_retrieval")
            # Extract key clinical context for query
            # We prioritize Assessment and History
            query_parts = []
            hpi = self._extract_hpi_fallback(extracted)
            if hpi: query_parts.append(hpi[:200]) # Limit length
            
            assessment = self._extract_section(extracted, "DOCTOR'S ASSESSMENT")
            if assessment and assessment != "Not mentioned":
                 query_parts.append(assessment)
            
            rag_query = " ".join(query_parts)
            self.logger.info(f"RAG Query: '{rag_query}'")
            
            if len(rag_query) > 10:
                retrieved = self.rag.retrieve(rag_query, k=2)
                guidelines_text = self.rag.format_for_prompt(retrieved)
                if guidelines_text:
                    self.logger.info(f"RAG Retrieved {len(retrieved)} guidelines.")

        # Stage 2: Structuring (Pass 2)
        self.logger.info("two_pass_summarizer | stage=2 | action=structuring")
        
        # Self-Learning: Inject physician's learned preferences + recent corrections
        style_guide = self._get_physician_style_guide()
        contextual_few_shot = TEMPLATE_STYLE
        if style_guide:
            contextual_few_shot = style_guide + "\n" + TEMPLATE_STYLE

        structuring_prompt = STRUCTURING_PROMPT.format(
            few_shot_examples=contextual_few_shot,
            extracted_info=extracted,
            guidelines=guidelines_text
        )
        structured = self._invoke_model(structuring_prompt, temperature=0.2) # Increased for more descriptive flow
        # Strip conversational filler
        structured = self._strip_conversational_prefix(structured)

        # Prepend the HPI header if missing
        if not structured.strip().startswith("HPI"):
             structured = "HPI (History of Present Illness):\n" + structured

        final_note = structured # Initialize final_note with the structured output

        # Stage 3: Self-Correction (BYPASSED)
        # We bypass Stage 3 because it often over-deletes valid clinical data in local models (e.g. erasing LMP/cycles)
        final_note = structured 

        # 4. Final Formatting & Cleanup
        # Ensure HPI is always at the top even after corrections
        if not final_note.strip().startswith("HPI"):
             final_note = self._strip_conversational_prefix(final_note)

        final_summary_text = process_summary(final_note)
        final_summary_text = self._enforce_structure(final_summary_text)

        runtime = time.perf_counter() - start_time

        hpi = self._extract_section(final_summary_text, "HPI")
        # Fix repeated header hallucination
        if "(History of Present Illness):" in hpi:
             hpi = hpi.replace("(History of Present Illness):", "").strip()
        
        # Fallback if HPI is missing/empty/too short
        if not hpi or len(hpi) < 10:
            self.logger.warning("HPI missing in structured output, attempting fallback from raw extraction...")
            fallback = self._extract_hpi_fallback(extracted)
            if fallback:
                hpi = fallback
                self.logger.info("Fallback HPI extracted.")

        return StructuredSummary(
            hpi=hpi,
            findings=self._extract_bullet_section(final_summary_text, "Findings"),
            assessment=self._extract_bullet_section(final_summary_text, "Assessment"),
            plan=self._extract_bullet_section(final_summary_text, "Plan"),
            medications=self._extract_bullet_section(final_summary_text, "Medications"),
            followup=self._extract_section(final_summary_text, "Follow-up"),
            raw_extraction=extracted,
            runtime_s=runtime,
            model_used=self.config.model,
        )

    def _get_feedback_examples(self) -> str:
        """Retrieve recent summary feedback to guide the LLM's style."""
        try:
            with self.db._get_connection() as conn:
                import sqlite3
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT original_content, edited_content FROM feedback WHERE field = 'summary' ORDER BY timestamp DESC LIMIT 2"
                )
                rows = cursor.fetchall()
                if not rows:
                    return ""
                
                examples = []
                for i, row in enumerate(rows):
                    examples.append(f"Correction {i+1}:\n- INSTEAD OF: {row['original_content'][:200]}...\n- USE STYLE: {row['edited_content'][:500]}")
                
                return "\n\n".join(examples)
        except Exception as e:
            self.logger.warning(f"Could not load feedback examples: {e}")
            return ""

    def _get_physician_style_guide(self) -> str:
        """Build a comprehensive style guide from learned preferences + recent corrections."""
        parts = []

        # 1. Structured preferences from the DB
        pref_prompt = self.db.get_preference_prompt()
        if pref_prompt:
            parts.append(pref_prompt)

        # 2. Concrete correction examples (last 2)
        examples = self._get_feedback_examples()
        if examples:
            parts.append("### RECENT CORRECTION EXAMPLES:\n" + examples)

        if not parts:
            return ""

        return "\n\n".join(parts)

    def summarize_text(self, transcript: str, style: Optional[str] = None) -> str:
        """Generate summary and return as formatted text."""
        result = self.summarize(transcript, style)
        return self._format_structured_summary(result)

    SPEAKER_MAPPING_PROMPT = """[INST] <<SYS>>
    You are a logic engine. Analyze the following transcript to identify the role of each speaker.
    Map "SPEAKER_00", "SPEAKER_01", etc. to "Doctor" and "Patient".
    
    Output ONLY a JSON object. Example: {{"SPEAKER_00": "Doctor", "SPEAKER_01": "Patient"}}
    <</SYS>>
    
    Transcript snippet:
    {snippet}
    
    JSON Output:
    [/INST]"""

    def diarize(self, transcript: str) -> str:
        """
        Converts a raw transcript into a structured conversation.
        If already diarized (GIEar/WhisperX), just maps labels to Doctor/Patient.
        Otherwise, uses LLM to format and label.
        """
        if not transcript or not transcript.strip():
            return transcript

        # Check for pre-diarized format (e.g. "[00:00] SPEAKER_00:")
        if "SPEAKER_" in transcript and "]" in transcript:
            self.logger.info("two_pass_summarizer | action=diarize | method=mapping_only")
            return self._map_speakers(transcript)

        prompt = DIARIZATION_PROMPT.format(transcript=transcript)
        
        self.logger.info("two_pass_summarizer | action=diarize | method=full_generation")
        return self._invoke_model(prompt, temperature=0.1)

    def _map_speakers(self, transcript: str) -> str:
        """Maps SPEAKER_XX to Doctor/Patient using a quick LLM check."""
        # Take a snippet from the middle to ensure we capture checking/questions which helps Identify roles
        # The start might be merged or ambiguous.
        mid_point = len(transcript) // 2
        # Ensure we don't go out of bounds
        start = max(0, mid_point - 1000)
        end = min(len(transcript), start + 2000)
        
        snippet = transcript[start:end]
        prompt = self.SPEAKER_MAPPING_PROMPT.format(snippet=snippet)
        
        try:
            response = self._invoke_model(prompt, temperature=0.1)
            # Naive parsing of JSON-like response
            import json
            # Try to find JSON block
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                mapping = json.loads(match.group(0))
                result = transcript
                for spk, role in mapping.items():
                    # Replace SPEAKER_XX with Role
                    result = result.replace(spk, role)
                return result
        except Exception as e:
            self.logger.warning(f"Speaker mapping failed: {e}. Returning original.")
        
        return transcript

    def _invoke_model(self, prompt: str, temperature: float = 0.05) -> str:
        """Invoke the model with optimized parameters."""
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "stop": ["[/INST]", "User:", "Observation:", "### System:", "### User:", "### Instruction:"],
            "options": {
                "temperature": temperature,
                "num_predict": self.config.max_tokens,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.15,
                "num_thread": 8,
                "num_ctx": max(getattr(self.config, "context_window", 4096), 4096),
            },
        }

        start = time.perf_counter()
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self._endpoint,
                    json=payload,
                    timeout=max(self.config.timeout_s, 300),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "").strip()
                
                if not text:
                    raise ValueError("Empty response from model")
                
                # Debugging: Print for immediate visibility in terminal
                print(f"\n--- LLM RAW RESPONSE ---\n{text}\n-----------------------\n")
                
                runtime = time.perf_counter() - start

                return text

            except requests.RequestException as exc:
                self.logger.warning(f"Model invocation failed (attempt {attempt + 1}): {exc}")
                if attempt < self.max_retries - 1:
                    time.sleep(1.0 * (attempt + 1))
                else:
                    raise

    def _enforce_structure(self, summary: str) -> str:
        """Ensure mandatory sections are present; allow optional ones to be omitted."""
        mandatory_sections = [
            ("HPI (History of Present Illness):", "HPI:"),
            ("Assessment:", "Assessment:"),
        ]

        result = summary
        summary_lower = summary.lower()

        for full_name, short_name in mandatory_sections:
            clean_summary = summary_lower.replace("*", "").replace(":", "")
            clean_full = full_name.lower().replace(":", "")
            clean_short = short_name.lower().replace(":", "")
            
            has_section = (
                clean_full in clean_summary or
                clean_short in clean_summary
            )
            
            if not has_section:
                result += f"\n\n{full_name}\nNot documented"

        return result

    def _strip_conversational_prefix(self, text: str) -> str:
        """Remove conversational filler by locating the start of the note."""
        # Find the start of the HPI section
        match = re.search(r"(HPI|History of Present Illness)", text, re.IGNORECASE)
        if match:
            return text[match.start():].strip()
        
        # Fallback to current behavior if HPI not found (unlikely)
        patterns = [
            r"^Here is the(?: formatted)?(?: clinical)? note:?",
            r"^Sure, here is the note:?",
            r"^Based on the transcript, here is the note:?",
            r"^Here's the extracted information:?",
            r"^Here is the summary:?",
        ]
        
        result = text.strip()
        for pattern in patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE).strip()
            
        return result

    def _extract_hpi_fallback(self, raw_text: str) -> str:
        """Fallback to extract HPI from raw extraction if structuring failed."""
        if not raw_text:
            return ""
        
        # Look for [HISTORY] or [CHIEF COMPLAINT] sections in the new tagged schema
        patterns = [
            r"\[HISTORY\]:?\s*\n?(.*?)(?=\n\[|$)",
            r"\[CHIEF COMPLAINT\]:?\s*\n?(.*?)(?=\n\[|$)",
            r"PATIENT HISTORY:?\s*\n(.*?)(?=\n\d+\.|\n[A-Z]+|$)",
            r"History:?\s*\n(.*?)(?=\n\d+\.|\n[A-Z]+|$)"
        ]
        
        extracted_parts = []
        for pattern in patterns:
            match = re.search(pattern, raw_text, re.DOTALL | re.IGNORECASE)
            if match:
                clean = match.group(1).strip()
                if clean and "not documented" not in clean.lower():
                    extracted_parts.append(clean)
        
        if extracted_parts:
             return " ".join(extracted_parts)
        return ""

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract content of a section as text."""
        patterns = [
            rf"{section_name}[^:]*:\s*\n?(.*?)(?=\n[A-Z][a-z]+[^:]*:|\n\*\*|\n###|$)",
            rf"\*\*{section_name}[^*]*\*\*[:]?\s*\n?(.*?)(?=\n\*\*|\n###|$)",
            rf"\*\*{section_name}[^*]*\*\*[:]?\s*\n?(.*?)(?=\n[A-Z][a-z]+[^:]*:|\n###|$)",
            rf"###\s*{section_name}[^:\n]*:?\s*\n?(.*?)(?=\n###|\n\*\*|$)",
            rf"^{section_name}:\s*(.*?)(?=\n[A-Z]|$)", # Simple start of line
        ]
        
        # Try a more aggressive regex if the ones above fail
        # This one just looks for the word followed by optional colon/bolding
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
                if match:
                    content = match.group(1).strip()
                    if content and len(content) > 3: # Ignore very short artifacts
                         return content
            except Exception as e:
                self.logger.debug(f"Regex match failed for {section_name}: {e}")
        
        # Last resort: just find the word and take everything until next logical break
        # We look for section names as discrete blocks
        text_lines = text.split('\n')
        for i, line in enumerate(text_lines):
            if section_name.lower() in line.lower() and (':' in line or '**' in line):
                # We found a potential start
                content_lines = []
                for j in range(i + 1, len(text_lines)):
                    # Stop if we see a new header
                    if re.match(r"^[A-Z][a-z]+(\s+[A-Za-z]+)*:", text_lines[j].strip()):
                        break
                    if "**" in text_lines[j] and ":" in text_lines[j]:
                        break
                    content_lines.append(text_lines[j])
                
                res = "\n".join(content_lines).strip()
                if res: return res

        return "Not documented"

    def _extract_bullet_section(self, text: str, section_name: str) -> List[str]:
        """Extract content of a section as bullet points."""
        content = self._extract_section(text, section_name)
        if content == "Not documented":
            return ["Not documented"]
        
        # Split by bullet points or numbered lists
        items = re.split(r'\n[-•*]\s*|\n\d+\.\s*', content)
        items = [item.strip() for item in items if item.strip()]
        # If not found after common markers, try a more aggressive regex for anything before 'Findings' or 'Assessment'
        if not items:
            hpi_match = re.search(r'(?:HPI|History of Present Illness)\s*:(.*?)(?=\s*(?:Findings|Assessment|Plan|Medications|Orders|Follow-up)|$)', text, re.IGNORECASE | re.DOTALL)
            if hpi_match:
                content = hpi_match.group(1).strip()
                if content:
                    return [content]
        
        return items if items else []

    def _is_meaningful(self, text: Any) -> bool:
        """Check if a section has actual clinical content beyond 'none' or 'not documented'."""
        if not text:
            return False
            
        # Convert list to string for uniform checking
        str_text = " ".join(text) if isinstance(text, list) else str(text)
        str_text_lower = str_text.lower().strip()
        
        # Omission markers
        empty_markers = [
            "not documented", 
            "none currently prescribed", 
            "none reported", 
            "none prescribed",
            "* none",
            "- none",
            "not mentioned",
            "none"
        ]
        
        # Explicit check for "None" or "Not documented"
        if any(marker in str_text_lower for marker in empty_markers) and len(str_text_lower) < 30:
            return False
            
        return len(str_text_lower) > 3

    def _format_structured_summary(self, result: StructuredSummary) -> str:
        """Format structured summary back to text, skipping empty/filler sections."""
        sections = []
        seen_content = set()
        
        def is_repetitive(content: str) -> bool:
            clean = content.lower().strip()
            if clean in seen_content and len(clean) > 20:
                return True
            seen_content.add(clean)
            return False

        # Mandatory HPI
        if self._is_meaningful(result.hpi):
            sections.append(f"HPI (History of Present Illness):\n{result.hpi}")
            is_repetitive(result.hpi)
        
        # Optional sections
        if self._is_meaningful(result.findings) and not is_repetitive(" ".join(result.findings)):
            findings_text = "\n".join(f"- {f}" for f in result.findings)
            sections.append(f"Findings:\n{findings_text}")
        
        # Mandatory Assessment
        if self._is_meaningful(result.assessment) and not is_repetitive(" ".join(result.assessment)):
            assessment_text = "\n".join(f"{i+1}. {a}" for i, a in enumerate(result.assessment))
            sections.append(f"Assessment:\n{assessment_text}")
        
        # Optional sections
        if self._is_meaningful(result.plan) and not is_repetitive(" ".join(result.plan)):
            plan_text = "\n".join(f"- {p}" for p in result.plan)
            sections.append(f"Plan:\n{plan_text}")
        
        if self._is_meaningful(result.medications) and not is_repetitive(" ".join(result.medications)):
            meds_text = "\n".join(f"- {m}" for m in result.medications)
            sections.append(f"Medications/Orders:\n{meds_text}")
        
        if self._is_meaningful(result.followup) and not is_repetitive(result.followup):
            sections.append(f"Follow-up:\n- {result.followup}")
        
        return "\n\n".join(sections)
