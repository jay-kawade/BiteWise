"""Tests for src/scanner/nutrition_parser.py."""

from src.scanner.nutrition_parser import parse_nutrition_text

SAMPLE_LABEL = """
Nutrition Facts
Serving Size 40g
Calories 190
Total Fat 8g
Saturated Fat 3.5g
Sodium 210mg
Total Carbohydrate 25g
Dietary Fiber 2g
Sugars 12g
Protein 4g
"""

TYPO_LABEL = """
Calorles 190
Proteln 4g
Total Carbohydrate 25g
Total Fat 8g
"""

MALFORMED_LABEL = """
This is not a nutrition label at all. Just some random text about a recipe.
"""


def test_parses_all_core_fields_from_clean_label():
    result = parse_nutrition_text(SAMPLE_LABEL, ocr_confidence=0.95)
    assert result.values["calories"] == 190.0
    assert result.values["protein_g"] == 4.0
    assert result.values["carbohydrates_g"] == 25.0
    assert result.values["fat_g"] == 8.0
    assert result.values["sodium_mg"] == 210.0
    assert result.overall_confidence > 0.7


def test_tolerates_common_ocr_typos_via_fuzzy_matching():
    result = parse_nutrition_text(TYPO_LABEL, ocr_confidence=0.6)
    # "Calorles" and "Proteln" should still be recognized.
    assert result.values.get("calories") == 190.0
    assert result.values.get("protein_g") == 4.0
    # Fuzzy matches must be flagged as warnings for the user to verify.
    assert any("fuzzy" in w.lower() for w in result.warnings)


def test_malformed_label_does_not_crash_and_reports_low_confidence():
    result = parse_nutrition_text(MALFORMED_LABEL, ocr_confidence=0.3)
    assert result.values == {}
    assert result.overall_confidence < 0.5
    assert any("low" in w.lower() for w in result.warnings)


def test_empty_text_does_not_crash():
    result = parse_nutrition_text("", ocr_confidence=0.0)
    assert result.values == {}
    assert result.overall_confidence == 0.0
