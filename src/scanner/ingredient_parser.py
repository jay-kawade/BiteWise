"""
ingredient_parser.py
-------------------------------------------------------------------------------
Extracts the ingredient list from OCR text and checks it against the user's
allergies / ingredients-to-avoid (Section 9: Ingredient Analysis).

IMPORTANT SAFETY LANGUAGE (Section 9 of the spec, not optional):
This is LABEL-TEXT matching only. It does not verify the physical product,
does not detect cross-contamination, and cannot guarantee allergen safety.
Every warning produced by this module must be phrased as a "potential
match" and must tell the user to check the physical packaging and consult a
qualified professional for serious allergies. See ALLERGEN_DISCLAIMER below,
which is reused verbatim by the UI.
-------------------------------------------------------------------------------
"""

import re
from dataclasses import dataclass, field
from typing import List

from rapidfuzz import fuzz

ALLERGEN_DISCLAIMER = (
    "Potential ingredient match detected based on the scanned label text only. "
    "This does not guarantee the product is safe or unsafe -- please check the "
    "original packaging and consult a qualified healthcare professional if you "
    "have a serious allergy."
)

FUZZY_INGREDIENT_THRESHOLD = 85

# A small, controlled vocabulary of common allergen keywords and the words
# that typically indicate them on a label. This is NOT an exhaustive medical
# allergen list -- it covers the common allergens used elsewhere in this
# project's controlled vocabulary (see data/sample/README.md).
ALLERGEN_KEYWORDS = {
    "milk": ["milk", "milk solids", "milk powder", "dairy", "casein", "whey", "lactose", "butter", "ghee", "cheese"],
    "egg": ["egg", "eggs", "albumin"],
    "gluten": ["wheat", "wheat flour", "gluten", "barley", "rye", "maida", "semolina"],
    "peanut": ["peanut", "peanuts", "groundnut"],
    "tree_nut": ["almond", "cashew", "walnut", "pistachio", "hazelnut", "tree nut"],
    "soy": ["soy", "soya", "soy lecithin", "soybean"],
    "shellfish": ["shrimp", "prawn", "crab", "lobster", "shellfish"],
    "fish": ["fish", "anchovy", "tuna", "salmon extract"],
}


@dataclass
class AllergenWarning:
    allergen_or_term: str
    matched_ingredient_text: str
    match_type: str   # "exact" or "fuzzy"
    match_score: float


@dataclass
class IngredientParseResult:
    ingredients: List[str] = field(default_factory=list)
    detected_allergens: List[str] = field(default_factory=list)  # from the controlled vocabulary
    warnings: List[AllergenWarning] = field(default_factory=list)


def extract_ingredient_list(ocr_text: str) -> List[str]:
    """
    Looks for a line starting with "ingredients" and splits everything after
    it on commas. Handles the common label format:
        "Ingredients: Wheat flour, sugar, cocoa, peanut..."
    """
    # Require a colon/dash right after the word "ingredients" so this only
    # matches an actual label heading (e.g. "Ingredients:") and not the word
    # appearing incidentally inside unrelated prose.
    match = re.search(r"ingredients\s*[:\-]\s*(.+)", ocr_text, re.IGNORECASE | re.DOTALL)
    if not match:
        return []
    raw = match.group(1)
    # Stop at the next all-caps label-style heading if present (e.g. "ALLERGEN INFO")
    raw = re.split(r"\n[A-Z][A-Z ]{4,}", raw)[0]
    parts = re.split(r"[,;]", raw)
    ingredients = []
    for part in parts:
        cleaned = part.strip().strip(".").strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        if cleaned and len(cleaned) < 60:
            ingredients.append(cleaned)
    return ingredients


def check_allergens_and_restrictions(
    ingredients: List[str],
    user_allergies: List[str],
    user_avoid_ingredients: List[str],
) -> IngredientParseResult:
    result = IngredientParseResult(ingredients=ingredients)

    ingredient_text_joined = " | ".join(ingredients).lower()

    # 1. Controlled-vocabulary allergen detection (milk, egg, gluten, ...).
    for allergen, keywords in ALLERGEN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in ingredient_text_joined:
                result.detected_allergens.append(allergen)
                result.warnings.append(AllergenWarning(
                    allergen_or_term=allergen, matched_ingredient_text=keyword,
                    match_type="exact", match_score=100.0,
                ))
                break

    # 2. User-specific free-text allergies / avoid-ingredients, matched
    #    against each parsed ingredient (exact substring, then fuzzy).
    user_terms = [(t, "allergy") for t in user_allergies] + [(t, "avoid_ingredient") for t in user_avoid_ingredients]
    for term, _kind in user_terms:
        term_lower = term.strip().lower()
        if not term_lower:
            continue
        matched = False
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            if term_lower in ingredient_lower:
                result.warnings.append(AllergenWarning(
                    allergen_or_term=term, matched_ingredient_text=ingredient,
                    match_type="exact", match_score=100.0,
                ))
                matched = True
                break
            score = fuzz.partial_ratio(term_lower, ingredient_lower)
            if score >= FUZZY_INGREDIENT_THRESHOLD:
                result.warnings.append(AllergenWarning(
                    allergen_or_term=term, matched_ingredient_text=ingredient,
                    match_type="fuzzy", match_score=score,
                ))
                matched = True
                break
        if not matched:
            continue

    return result
