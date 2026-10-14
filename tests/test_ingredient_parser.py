"""Tests for src/scanner/ingredient_parser.py."""

from src.scanner.ingredient_parser import check_allergens_and_restrictions, extract_ingredient_list

LABEL_TEXT = """
Nutrition Facts
Calories 190
Ingredients: Wheat flour, sugar, palm oil, cocoa solids, milk solids, peanut,
salt, raising agents, emulsifiers (soy lecithin), artificial flavour.
"""


def test_extract_ingredient_list_splits_on_commas():
    ingredients = extract_ingredient_list(LABEL_TEXT)
    assert "Wheat flour" in ingredients
    assert "sugar" in ingredients
    assert "peanut" in ingredients
    assert len(ingredients) >= 8


def test_extract_ingredient_list_no_ingredients_section_returns_empty():
    assert extract_ingredient_list("Just some random text with no ingredients heading.") == []


def test_detects_controlled_vocabulary_allergens():
    ingredients = extract_ingredient_list(LABEL_TEXT)
    result = check_allergens_and_restrictions(ingredients, user_allergies=[], user_avoid_ingredients=[])
    assert "milk" in result.detected_allergens
    assert "gluten" in result.detected_allergens  # from "wheat flour"
    assert "peanut" in result.detected_allergens
    assert "soy" in result.detected_allergens


def test_detects_user_specific_allergy_exact_match():
    ingredients = extract_ingredient_list(LABEL_TEXT)
    result = check_allergens_and_restrictions(ingredients, user_allergies=["peanut"], user_avoid_ingredients=[])
    matched_terms = [w.allergen_or_term for w in result.warnings]
    assert "peanut" in matched_terms


def test_no_false_positive_for_unrelated_allergy():
    ingredients = extract_ingredient_list(LABEL_TEXT)
    result = check_allergens_and_restrictions(ingredients, user_allergies=["shellfish"], user_avoid_ingredients=[])
    matched_terms = [w.allergen_or_term for w in result.warnings]
    assert "shellfish" not in matched_terms


def test_empty_ingredient_list_produces_no_warnings():
    result = check_allergens_and_restrictions([], user_allergies=["peanut"], user_avoid_ingredients=[])
    assert result.warnings == []
    assert result.detected_allergens == []
