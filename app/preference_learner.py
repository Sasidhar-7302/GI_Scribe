"""
Preference Learner
==================
Analyzes diffs between physician-corrected and original summaries to
extract named style preferences. No LLM needed — uses diff + pattern matching.
"""

import difflib
import re
import logging
from typing import List, Tuple

from .database import DatabaseManager

logger = logging.getLogger("medrec.preference_learner")

# Section headers we look for in clinical notes
SECTION_HEADERS = ["HPI", "Findings", "Assessment", "Plan", "Medications", "Follow-up"]


class PreferenceLearner:
    """Extracts physician preferences from original→edited summary diffs."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def learn_from_correction(self, original: str, edited: str,
                              physician_id: str = "default") -> List[Tuple[str, str, str]]:
        """
        Compare original vs edited summary and extract preferences.
        Returns list of (category, key, value) tuples that were learned.
        """
        if not original or not edited:
            return []

        learned: List[Tuple[str, str, str]] = []

        # 1. Structural preferences
        learned += self._detect_section_changes(original, edited)

        # 2. Style preferences
        learned += self._detect_style_changes(original, edited)

        # 3. Terminology preferences
        learned += self._detect_terminology_changes(original, edited)

        # 4. Detail level preferences
        learned += self._detect_detail_changes(original, edited)

        # Persist all learned preferences
        for category, key, value in learned:
            self.db.upsert_preference(category, key, value, physician_id)
            logger.info(f"Learned preference: [{category}] {key} = {value}")

        return learned

    def _detect_section_changes(self, original: str, edited: str) -> List[Tuple[str, str, str]]:
        """Detect changes in section ordering, addition, or removal."""
        learned = []

        orig_sections = self._extract_section_order(original)
        edit_sections = self._extract_section_order(edited)

        if orig_sections != edit_sections and edit_sections:
            learned.append(("structure", "section_order", " → ".join(edit_sections)))

        # Detect if physician removed empty/placeholder sections
        orig_has_not_doc = original.lower().count("not documented")
        edit_has_not_doc = edited.lower().count("not documented")
        if orig_has_not_doc > edit_has_not_doc and edit_has_not_doc == 0:
            learned.append(("structure", "omit_empty_sections", "true"))

        return learned

    def _detect_style_changes(self, original: str, edited: str) -> List[Tuple[str, str, str]]:
        """Detect HPI format, verbosity, and writing style preferences."""
        learned = []

        # HPI format: bullets vs narrative
        orig_hpi = self._extract_section_text(original, "HPI")
        edit_hpi = self._extract_section_text(edited, "HPI")

        if orig_hpi and edit_hpi:
            orig_has_bullets = bool(re.search(r"^[\s]*[-•]", orig_hpi, re.MULTILINE))
            edit_has_bullets = bool(re.search(r"^[\s]*[-•]", edit_hpi, re.MULTILINE))

            if orig_has_bullets and not edit_has_bullets:
                learned.append(("style", "hpi_format", "narrative_paragraph"))
            elif not orig_has_bullets and edit_has_bullets:
                learned.append(("style", "hpi_format", "bullet_points"))

            # Verbosity: compare relative length
            ratio = len(edit_hpi) / max(len(orig_hpi), 1)
            if ratio < 0.6:
                learned.append(("style", "hpi_verbosity", "concise"))
            elif ratio > 1.5:
                learned.append(("style", "hpi_verbosity", "detailed"))

        # Assessment style: numbered with evidence vs simple list
        edit_assessment = self._extract_section_text(edited, "Assessment")
        if edit_assessment:
            has_numbers = bool(re.search(r"^\s*\d+\.", edit_assessment, re.MULTILINE))
            has_evidence = bool(re.search(r"(?:supported by|evidenced by|per |based on)", edit_assessment, re.IGNORECASE))
            if has_numbers and has_evidence:
                learned.append(("style", "assessment_style", "numbered_with_evidence"))
            elif has_numbers:
                learned.append(("style", "assessment_style", "numbered_list"))

        # Follow-up style
        orig_fu = self._extract_section_text(original, "Follow-up")
        edit_fu = self._extract_section_text(edited, "Follow-up")
        if orig_fu and edit_fu:
            if len(edit_fu) < len(orig_fu) * 0.5:
                learned.append(("style", "followup_style", "concise"))

        return learned

    def _detect_terminology_changes(self, original: str, edited: str) -> List[Tuple[str, str, str]]:
        """Detect abbreviation usage patterns and term substitutions."""
        learned = []

        # Common medical abbreviation patterns
        abbreviation_map = {
            "history of present illness": "HPI",
            "blood pressure": "BP",
            "twice daily": "BID",
            "three times daily": "TID",
            "as needed": "PRN",
            "review of systems": "ROS",
            "physical exam": "PE",
            "right upper quadrant": "RUQ",
            "left lower quadrant": "LLQ",
        }

        orig_lower = original.lower()
        edit_lower = edited.lower()

        # Check if physician expanded abbreviations (prefers full terms)
        expansions = 0
        abbreviations = 0
        for full, abbrev in abbreviation_map.items():
            if abbrev.lower() in orig_lower and full in edit_lower:
                expansions += 1
            if full in orig_lower and abbrev.lower() in edit_lower:
                abbreviations += 1

        if expansions > abbreviations and expansions >= 2:
            learned.append(("terminology", "uses_abbreviations", "false — prefers full terms"))
        elif abbreviations > expansions and abbreviations >= 2:
            learned.append(("terminology", "uses_abbreviations", "true — prefers standard abbreviations"))

        # Detect specific term substitutions using diff
        diff = list(difflib.unified_diff(
            original.splitlines(), edited.splitlines(), lineterm=""
        ))
        removals = [l[1:].strip() for l in diff if l.startswith("-") and not l.startswith("---")]
        additions = [l[1:].strip() for l in diff if l.startswith("+") and not l.startswith("+++")]

        # If physician consistently replaces a term, learn it
        if len(removals) == len(additions) and 1 <= len(removals) <= 5:
            for old, new in zip(removals, additions):
                # Only learn short, meaningful substitutions
                if 3 < len(old) < 80 and 3 < len(new) < 80 and old != new:
                    similarity = difflib.SequenceMatcher(None, old, new).ratio()
                    if 0.3 < similarity < 0.9:  # similar enough to be a substitution, not a rewrite
                        learned.append(("terminology", f"prefer_{new[:30]}", f"Instead of '{old[:40]}', use '{new[:40]}'"))
                        break  # learn at most one substitution per correction

        return learned

    def _detect_detail_changes(self, original: str, edited: str) -> List[Tuple[str, str, str]]:
        """Detect if physician adds/removes detail (e.g., drug doses, lab values)."""
        learned = []

        # Medication detail: did physician add doses?
        edit_meds = self._extract_section_text(edited, "Medications")
        orig_meds = self._extract_section_text(original, "Medications")

        if edit_meds and orig_meds:
            # Count dose-like patterns (e.g., "40mg", "800mg BID")
            orig_doses = len(re.findall(r"\d+\s*(?:mg|mcg|ml|g|units?)\b", orig_meds, re.IGNORECASE))
            edit_doses = len(re.findall(r"\d+\s*(?:mg|mcg|ml|g|units?)\b", edit_meds, re.IGNORECASE))
            if edit_doses > orig_doses + 1:
                learned.append(("detail_level", "medication_detail", "always_include_doses_and_frequency"))

        # Lab detail: did physician add specific values?
        orig_labs = len(re.findall(r"\d+(?:\.\d+)?\s*(?:mg/dL|g/dL|mmol|U/L|ng/mL)", original, re.IGNORECASE))
        edit_labs = len(re.findall(r"\d+(?:\.\d+)?\s*(?:mg/dL|g/dL|mmol|U/L|ng/mL)", edited, re.IGNORECASE))
        if edit_labs > orig_labs + 1:
            learned.append(("detail_level", "lab_values", "include_specific_values"))

        return learned

    # ── Helpers ──────────────────────────────────────────────────────

    def _extract_section_order(self, text: str) -> List[str]:
        """Return the order of section headers found in text."""
        found = []
        for line in text.splitlines():
            stripped = line.strip().rstrip(":")
            for header in SECTION_HEADERS:
                if stripped.lower().startswith(header.lower()):
                    if header not in found:
                        found.append(header)
                    break
        return found

    def _extract_section_text(self, text: str, section_name: str) -> str:
        """Extract the content of a named section."""
        lines = text.splitlines()
        capture = False
        result = []
        for line in lines:
            stripped = line.strip().rstrip(":")
            if stripped.lower().startswith(section_name.lower()):
                capture = True
                continue
            if capture:
                # Stop at next section header
                is_header = any(stripped.lower().startswith(h.lower()) for h in SECTION_HEADERS)
                if is_header:
                    break
                result.append(line)
        return "\n".join(result).strip()
