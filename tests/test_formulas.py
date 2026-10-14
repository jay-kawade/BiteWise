"""Tests for src/nutrition/formulas.py -- the documented nutrition equations."""

import pytest

from src.nutrition import formulas


def test_bmi_calculation():
    # 70kg, 175cm -> BMI = 70 / 1.75^2 = 22.9
    assert formulas.calculate_bmi(70, 175) == pytest.approx(22.9, abs=0.05)


def test_bmi_invalid_height_raises():
    with pytest.raises(ValueError):
        formulas.calculate_bmi(70, 0)


@pytest.mark.parametrize("bmi,expected", [
    (17.0, "Underweight"),
    (18.5, "Normal weight"),
    (24.9, "Normal weight"),
    (25.0, "Overweight"),
    (29.9, "Overweight"),
    (30.0, "Obese"),
    (40.0, "Obese"),
])
def test_bmi_classification_boundaries(bmi, expected):
    assert formulas.classify_bmi(bmi) == expected


def test_bmr_male_vs_female_formula():
    # Same weight/height/age, only sex differs -> female result should be
    # exactly 166 kcal lower than male (5 - (-161) = 166), per the equation.
    bmr_male = formulas.calculate_bmr(weight_kg=70, height_cm=175, age_years=25, sex="male")
    bmr_female = formulas.calculate_bmr(weight_kg=70, height_cm=175, age_years=25, sex="female")
    assert bmr_male - bmr_female == pytest.approx(166, abs=0.1)


def test_bmr_other_sex_is_average_of_male_and_female():
    bmr_male = formulas.calculate_bmr(70, 175, 25, "male")
    bmr_female = formulas.calculate_bmr(70, 175, 25, "female")
    bmr_other = formulas.calculate_bmr(70, 175, 25, "other")
    assert bmr_other == pytest.approx((bmr_male + bmr_female) / 2, abs=0.1)


def test_tdee_uses_correct_multiplier():
    bmr = 1500
    assert formulas.calculate_tdee(bmr, "sedentary") == pytest.approx(1500 * 1.2)
    assert formulas.calculate_tdee(bmr, "extremely_active") == pytest.approx(1500 * 1.9)


def test_tdee_invalid_activity_level_raises():
    with pytest.raises(ValueError):
        formulas.calculate_tdee(1500, "super_active")


def test_calorie_target_goal_adjustment():
    tdee = 2000
    assert formulas.calculate_calorie_target(tdee, "maintenance") == pytest.approx(2000)
    assert formulas.calculate_calorie_target(tdee, "weight_loss") == pytest.approx(1500)
    assert formulas.calculate_calorie_target(tdee, "weight_gain") == pytest.approx(2500)


def test_calorie_target_never_below_safety_floor():
    # A very low TDEE with a weight_loss goal should still be floored at 1200 kcal.
    assert formulas.calculate_calorie_target(1000, "weight_loss") == 1200


def test_protein_target_scales_with_weight_and_goal():
    assert formulas.calculate_protein_target(60, "maintenance") == pytest.approx(60 * 1.2)
    assert formulas.calculate_protein_target(60, "muscle_gain") == pytest.approx(60 * 1.8)


def test_fat_and_carb_targets_reconcile_with_calorie_target():
    calorie_target = 2000
    protein_g = 100
    fat_g = formulas.calculate_fat_target(calorie_target)
    carb_g = formulas.calculate_carb_target(calorie_target, protein_g, fat_g)

    total_kcal_from_macros = protein_g * 4 + fat_g * 9 + carb_g * 4
    assert total_kcal_from_macros == pytest.approx(calorie_target, abs=1.0)


def test_fiber_target_scales_with_calories():
    assert formulas.calculate_fiber_target(2000) == pytest.approx(28.0)
