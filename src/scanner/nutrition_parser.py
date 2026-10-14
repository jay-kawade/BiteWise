"""
nutrition_parser.py
-------------------------------------------------------------------------------
Turns raw OCR text (which is often messy: "Proteln 4g", "Calorles 190")
into structured nutrition values.

APPROACH:
1. For each nutrition field we care about, define the common label words
   that appear on real nutrition labels (e.g. "protein", "total protein").
2. For every line of OCR text, first try an EXACT (case-insensitive) match
   against those label words.
3. If no exact match is found on a line, try a FUZZY match (using
   rapidfuzz) against the same label words. This is what lets "Proteln"
   still be recognized as "Protein" -- but ONLY when the fuzzy similarity
   score is high enough (>= FUZZY_MATCH_THRESHOLD). This directly
   implements Section 8's requirement: OCR typos should be tolerated only
   when there is enough confidence, never silently guessed.
4. Extract the first number found on that same line as the value.
5. Track which fields were found via exact vs fuzzy match, and compute an
   overall parsing confidence score so the UI can warn the user when a
   field is uncertain and let them correct it manually.
-------------------------------------------------------------------------------
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from rapidfuzz import fuzz

FUZZY_MATCH_THRESHOLD = 82  # 0-100 scale; below this, we do not trust a fuzzy label match

# field_name -> list of label phrases that can appear on a real label
FIELD_LABELS: Dict[str, List[str]] = {
    "calories": ["calories", "energy", "energy value"],
    "protein_g": ["protein", "total protein"],
    "carbohydrates_g": ["total carbohydrate", "carbohydrate", "carbohydrates", "carbs"],
    "fat_g": ["total fat", "fat"],
    "saturated_fat_g": ["saturated fat", "of which saturates", "saturates"],
    "fiber_g": ["dietary fiber", "dietary fibre", "fiber", "fibre"],
    "sugar_g": ["sugars", "sugar", "of which sugars"],
    "sodium_mg": ["sodium"],
    "serving_size_g": ["serving size", "serving"],
}

# A number optionally followed by a unit, e.g. "190", "8g", "210mg", "160 kcal"
_NUMBER_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(kcal|mg|g)?", re.IGNORECASE)


@dataclass
class ParsedField:
    value: float
    unit: str
    match_type: str  # "exact" or "fuzzy"
    match_score: float
    source_line: str


@dataclass
class NutritionParseResult:
    values: Dict[str, float] = field(default_factory=dict)
    field_details: Dict[str, ParsedField] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    overall_confidence: float = 0.0


def _find_label_match(line_lower: str, field_name: str) -> Optional[tuple]:
    """Returns (matched_label, match_type, score) for the best label match on this line, or None."""
    best = None
    for label in FIELD_LABELS[field_name]:
        if label in line_lower:
            return (label, "exact", 100.0)
        score = fuzz.partial_ratio(label, line_lower)
        if score >= FUZZY_MATCH_THRESHOLD and (best is None or score > best[2]):
            best = (label, "fuzzy", score)
    return best


def _extract_number_after_label(line: str, label: str) -> Optional[tuple]:
    """Find the label's position in the line, then the first number appearing after it."""
    idx = line.lower().find(label)
    if idx != -1:
        remainder = line[idx + len(label):]
        match = _NUMBER_PATTERN.search(remainder)
        if match:
            return float(match.group(1)), (match.group(2) or "").lower()

    # Fallback: either the label text wasn't found verbatim (this happens for
    # a FUZZY match, e.g. "Proteln" matched against "protein" -- the exact
    # string "protein" never appears in the line) or no number followed it.
    # In both cases, just take the first number on the line.
    match = _NUMBER_PATTERN.search(line)
    if not match:
        return None
    return float(match.group(1)), (match.group(2) or "").lower()


def parse_nutrition_text(ocr_text: str, ocr_confidence: float = 1.0) -> NutritionParseResult:
    result = NutritionParseResult()
    lines = [ln.strip() for ln in ocr_text.splitlines() if ln.strip()]

    for field_name in FIELD_LABELS:
        found = False
        for line in lines:
            line_lower = line.lower()
            match = _find_label_match(line_lower, field_name)
            if not match:
                continue
            label, match_type, score = match
            extracted = _extract_number_after_label(line, label)
            if not extracted:
                continue
            value, unit = extracted

            result.values[field_name] = value
            result.field_details[field_name] = ParsedField(
                value=value, unit=unit, match_type=match_type, match_score=score, source_line=line
            )
            if match_type == "fuzzy":
                result.warnings.append(
                    f"'{field_name}' was matched from OCR text via fuzzy text matching "
                    f"(similarity {score:.0f}%) on the line: \"{line}\". Please verify this value."
                )
            found = True
            break
        if not found:
            result.warnings.append(f"Could not find '{field_name.replace('_', ' ')}' in the scanned text.")

    # Overall confidence blends: (a) how many core fields were found, and
    # (b) the OCR engine's own text-recognition confidence. This is a
    # simple, transparent formula -- not a trained model.
    core_fields = ["calories", "protein_g", "carbohydrates_g", "fat_g"]
    found_core = sum(1 for f in core_fields if f in result.values)
    field_coverage = found_core / len(core_fields)
    result.overall_confidence = round(0.6 * field_coverage + 0.4 * ocr_confidence, 3)

    if result.overall_confidence < 0.5:
        result.warnings.append(
            "Overall parsing confidence is LOW. Please review and correct the values below before relying on them."
        )

    return result
