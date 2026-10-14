"""Tests for src/nutrition/food_suitability.py."""

from src.nutrition.food_suitability import analyze_food_suitability


def test_matching_diet_type_gets_checkmark():
    result = analyze_food_suitability(
        nutrition={"calories": 200, "protein_g": 15, "carbohydrates_g": 20, "fat_g": 5, "sugar_g": 2, "sodium_mg": 100},
        diet_type="vegetarian", food_dietary_type="vegan",
        food_allergen_warnings=[], remaining_calorie_budget=1000, remaining_protein_budget=50,
    )
    assert any(item.symbol == ":material/check_circle:" and "fit" in item.text.lower() for item in result.checklist)
    assert "may not align" not in result.suitability_label.lower()


def test_mismatched_diet_type_gets_cross():
    result = analyze_food_suitability(
        nutrition={"calories": 200, "protein_g": 15, "carbohydrates_g": 20, "fat_g": 5, "sugar_g": 2, "sodium_mg": 100},
        diet_type="vegan", food_dietary_type="non_vegetarian",
        food_allergen_warnings=[], remaining_calorie_budget=1000, remaining_protein_budget=50,
    )
    assert any(item.symbol == ":material/cancel:" for item in result.checklist)


def test_allergen_warning_lowers_suitability():
    result = analyze_food_suitability(
        nutrition={"calories": 200, "protein_g": 15, "carbohydrates_g": 20, "fat_g": 5, "sugar_g": 2, "sodium_mg": 100},
        diet_type="vegetarian", food_dietary_type="vegetarian",
        food_allergen_warnings=["peanut (matched)"], remaining_calorie_budget=1000, remaining_protein_budget=50,
    )
    assert any("peanut" in item.text.lower() for item in result.checklist)


def test_high_sugar_and_sodium_are_flagged():
    result = analyze_food_suitability(
        nutrition={"calories": 300, "protein_g": 2, "carbohydrates_g": 40, "fat_g": 5, "sugar_g": 25, "sodium_mg": 600},
        diet_type="vegetarian", food_dietary_type=None,
        food_allergen_warnings=[], remaining_calorie_budget=1000, remaining_protein_budget=50,
    )
    texts = [item.text.lower() for item in result.checklist]
    assert any("sugar" in t for t in texts)
    assert any("sodium" in t for t in texts)


def test_never_claims_universally_healthy_or_unhealthy():
    result = analyze_food_suitability(
        nutrition={"calories": 200, "protein_g": 15, "carbohydrates_g": 20, "fat_g": 5, "sugar_g": 2, "sodium_mg": 100},
        diet_type="vegetarian", food_dietary_type="vegetarian",
        food_allergen_warnings=[], remaining_calorie_budget=1000, remaining_protein_budget=50,
    )
    label_lower = result.suitability_label.lower()
    assert "healthy" not in label_lower
    assert "unhealthy" not in label_lower
