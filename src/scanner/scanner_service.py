"""
scanner_service.py
-------------------------------------------------------------------------------
Orchestrates the full food-label scanning workflow described in Section 8:

    image bytes
        -> decode
        -> preprocess (image_preprocessor.py)
        -> OCR (ocr.py)
        -> parse nutrition values (nutrition_parser.py)
        -> parse + check ingredients/allergens (ingredient_parser.py)
        -> analyze against the user's profile (nutrition/food_suitability.py)
        -> return one structured result for the UI / agent to display

This is the single entry point the Streamlit "Food Scanner" page and the AI
agent's `analyze_scanned_label` tool both call, so the pipeline only needs
to be implemented once.
-------------------------------------------------------------------------------
"""

from dataclasses import dataclass
from typing import List, Optional

from src.database import repositories as repo
from src.database.models import ScannedFood
from src.nutrition.food_suitability import FoodSuitabilityResult, analyze_food_suitability
from src.scanner.image_preprocessor import decode_image_bytes, preprocess_image
from src.scanner.ingredient_parser import (
    ALLERGEN_DISCLAIMER,
    check_allergens_and_restrictions,
    extract_ingredient_list,
)
from src.scanner.nutrition_parser import parse_nutrition_text
from src.scanner.ocr import run_ocr
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScanResult:
    raw_ocr_text: str
    ocr_mode: str
    ocr_confidence: float
    parsed_nutrition: dict
    parsing_warnings: List[str]
    parsing_confidence: float
    ingredients: List[str]
    allergen_warnings: List[str]
    allergen_disclaimer: str
    suitability: Optional[FoodSuitabilityResult]
    scanned_food_id: Optional[int] = None


def scan_food_label(
    image_bytes: bytes,
    user_id: int,
    remaining_calorie_budget: Optional[float] = None,
    remaining_protein_budget: Optional[float] = None,
    save_to_history: bool = True,
) -> ScanResult:
    # 1-2. Decode + preprocess.
    image = decode_image_bytes(image_bytes)
    if image is not None:
        preprocess_result = preprocess_image(image)
        ocr_input_image = preprocess_result.image
    else:
        ocr_input_image = None
        logger.warning("Could not decode image bytes (OpenCV unavailable or invalid image); OCR will use mock mode.")

    # 3. OCR.
    ocr_result = run_ocr(ocr_input_image)

    # 4. Parse nutrition values.
    nutrition_parse = parse_nutrition_text(ocr_result.text, ocr_confidence=ocr_result.confidence)

    # 5. Parse ingredients + check allergens.
    ingredients = extract_ingredient_list(ocr_result.text)
    user_allergies = repo.get_preference_values(user_id, "allergy")
    user_avoid = repo.get_preference_values(user_id, "avoid_ingredient")
    ingredient_result = check_allergens_and_restrictions(ingredients, user_allergies, user_avoid)

    seen_terms = set()
    allergen_warning_strings = []
    for w in ingredient_result.warnings:
        key = (w.allergen_or_term.lower(), w.matched_ingredient_text.lower())
        if key in seen_terms:
            continue
        seen_terms.add(key)
        allergen_warning_strings.append(
            f"{w.allergen_or_term} (matched \"{w.matched_ingredient_text}\", {w.match_type} match)"
        )

    # 6. Analyze against the user's profile (Section 10).
    user = repo.get_user(user_id)
    suitability = None
    if user and nutrition_parse.values:
        suitability = analyze_food_suitability(
            nutrition=nutrition_parse.values,
            diet_type=user.diet_type,
            food_dietary_type=None,  # unknown from a label scan; dietary type isn't printed on nutrition labels
            food_allergen_warnings=allergen_warning_strings,
            remaining_calorie_budget=remaining_calorie_budget,
            remaining_protein_budget=remaining_protein_budget,
        )

    result = ScanResult(
        raw_ocr_text=ocr_result.text,
        ocr_mode=ocr_result.mode,
        ocr_confidence=ocr_result.confidence,
        parsed_nutrition=nutrition_parse.values,
        parsing_warnings=nutrition_parse.warnings,
        parsing_confidence=nutrition_parse.overall_confidence,
        ingredients=ingredient_result.ingredients,
        allergen_warnings=allergen_warning_strings,
        allergen_disclaimer=ALLERGEN_DISCLAIMER,
        suitability=suitability,
    )

    if save_to_history:
        scanned_food_id = repo.save_scanned_food(ScannedFood(
            id=None, user_id=user_id, raw_ocr_text=ocr_result.text,
            parsed_nutrition=nutrition_parse.values, parsed_ingredients=ingredient_result.ingredients,
            allergen_warnings=allergen_warning_strings, confidence_score=nutrition_parse.overall_confidence,
            ocr_mode=ocr_result.mode,
        ))
        result.scanned_food_id = scanned_food_id

    return result
