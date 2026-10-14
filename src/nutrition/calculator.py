"""
calculator.py
-------------------------------------------------------------------------------
This module orchestrates the individual formulas in formulas.py into one
easy-to-call function: compute_nutrition_targets(). It represents the
"deterministic nutrition calculation" layer of the app -- these are plain
arithmetic formulas, NOT machine learning (see src/ml/ for the ML component,
and docs/ml_methodology.md for how the two are kept clearly separate).
-------------------------------------------------------------------------------
"""

from dataclasses import dataclass

from src.database.models import UserProfile
from src.nutrition import formulas


@dataclass
class NutritionTargetsResult:
    bmi: float
    bmi_category: str
    bmr_kcal: float
    tdee_kcal: float
    calorie_target_kcal: float
    protein_target_g: float
    carb_target_g: float
    fat_target_g: float
    fiber_target_g: float


def compute_nutrition_targets(profile: UserProfile) -> NutritionTargetsResult:
    """
    Run the full deterministic nutrition calculation pipeline for one user
    profile. Every step is documented in src/nutrition/formulas.py.
    """
    bmi = formulas.calculate_bmi(profile.weight_kg, profile.height_cm)
    bmi_category = formulas.classify_bmi(bmi)

    bmr = formulas.calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.sex)
    tdee = formulas.calculate_tdee(bmr, profile.activity_level)
    calorie_target = formulas.calculate_calorie_target(tdee, profile.goal)

    protein_target = formulas.calculate_protein_target(profile.weight_kg, profile.goal)
    fat_target = formulas.calculate_fat_target(calorie_target)
    carb_target = formulas.calculate_carb_target(calorie_target, protein_target, fat_target)
    fiber_target = formulas.calculate_fiber_target(calorie_target)

    return NutritionTargetsResult(
        bmi=bmi,
        bmi_category=bmi_category,
        bmr_kcal=bmr,
        tdee_kcal=tdee,
        calorie_target_kcal=calorie_target,
        protein_target_g=protein_target,
        carb_target_g=carb_target,
        fat_target_g=fat_target,
        fiber_target_g=fiber_target,
    )


def summarize_consumed(food_log_entries) -> dict:
    """
    Sum up calories/macros from a list of FoodLogEntry objects (or anything
    with the same attribute names). Used by the daily tracker and the
    "what should I eat next" engine to know what has already been eaten.
    """
    totals = {
        "calories": 0.0, "protein_g": 0.0, "carbohydrates_g": 0.0,
        "fat_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0, "sodium_mg": 0.0,
    }
    for entry in food_log_entries:
        totals["calories"] += entry.calories
        totals["protein_g"] += entry.protein_g
        totals["carbohydrates_g"] += entry.carbohydrates_g
        totals["fat_g"] += entry.fat_g
        totals["fiber_g"] += entry.fiber_g
        totals["sugar_g"] += entry.sugar_g
        totals["sodium_mg"] += entry.sodium_mg
    return {k: round(v, 1) for k, v in totals.items()}


def calculate_remaining_targets(targets: NutritionTargetsResult, consumed: dict) -> dict:
    """
    Remaining = target - consumed, floored at 0 (we never show a negative
    "remaining" number; instead the UI should flag that the target was
    already met/exceeded).
    """
    return {
        "calories": round(max(targets.calorie_target_kcal - consumed["calories"], 0.0), 1),
        "protein_g": round(max(targets.protein_target_g - consumed["protein_g"], 0.0), 1),
        "carbohydrates_g": round(max(targets.carb_target_g - consumed["carbohydrates_g"], 0.0), 1),
        "fat_g": round(max(targets.fat_target_g - consumed["fat_g"], 0.0), 1),
        "fiber_g": round(max(targets.fiber_target_g - consumed["fiber_g"], 0.0), 1),
    }
