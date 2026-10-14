"""Tests for src/recommendation/meal_planner.py."""

import pytest

from src.database import repositories as repo
from src.database.models import NutritionTargets
from src.nutrition.calculator import compute_nutrition_targets
from src.recommendation.meal_planner import MEAL_SLOT_CALORIE_SHARE, generate_daily_meal_plan


def _give_user_targets(user_id):
    user = repo.get_user(user_id)
    result = compute_nutrition_targets(user)
    repo.save_nutrition_targets(NutritionTargets(
        id=None, user_id=user_id, bmi=result.bmi, bmi_category=result.bmi_category,
        bmr_kcal=result.bmr_kcal, tdee_kcal=result.tdee_kcal, calorie_target_kcal=result.calorie_target_kcal,
        protein_target_g=result.protein_target_g, carb_target_g=result.carb_target_g,
        fat_target_g=result.fat_target_g, fiber_target_g=result.fiber_target_g,
    ))


def test_meal_slot_shares_sum_to_one():
    assert sum(MEAL_SLOT_CALORIE_SHARE.values()) == pytest.approx(1.0)


def test_generate_daily_meal_plan_produces_one_item_per_slot(seeded_db, sample_user_id):
    _give_user_targets(sample_user_id)
    plan = generate_daily_meal_plan(sample_user_id)
    assert len(plan.items) == len(MEAL_SLOT_CALORIE_SHARE)


def test_generate_daily_meal_plan_reports_honest_difference(seeded_db, sample_user_id):
    _give_user_targets(sample_user_id)
    plan = generate_daily_meal_plan(sample_user_id)
    # The validation pass must be internally consistent: difference = total - target.
    assert plan.calorie_difference == pytest.approx(plan.total_calories - plan.target_calories, abs=0.1)
    assert plan.protein_difference == pytest.approx(plan.total_protein_g - plan.target_protein_g, abs=0.1)


def test_generate_daily_meal_plan_without_targets_raises(seeded_db, sample_user_id):
    # sample_user_id has no nutrition_targets row yet in this test.
    with pytest.raises(ValueError):
        generate_daily_meal_plan(sample_user_id)


def test_generate_daily_meal_plan_unknown_user_raises(seeded_db):
    with pytest.raises(ValueError):
        generate_daily_meal_plan(9999)
