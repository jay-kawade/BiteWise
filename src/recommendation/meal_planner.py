"""
meal_planner.py
-------------------------------------------------------------------------------
Implements Section 13: daily meal plan generation.

APPROACH (documented, not a black box):
1. The day's calorie/protein targets are split across 5 meal slots using a
   fixed, documented percentage allocation (see MEAL_SLOT_CALORIE_SHARE
   below). This mirrors common practical dietary advice of spreading intake
   across the day, and is a reasonable, simple assumption -- see
   ASSUMPTIONS.md.
2. For each slot, the best-fitting food (by the same transparent scoring
   function used for "what should I eat next") is greedily selected from the
   foods compatible with that meal slot, the user's diet type, allergies,
   and disliked foods.
3. After building the plan, run a validation pass that sums the actual
   totals and reports the difference from the target -- the app must never
   claim perfect nutritional accuracy (Section 13).
-------------------------------------------------------------------------------
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.database import repositories as repo
from src.database.models import Food
from src.recommendation.ranking import score_food_for_remaining_targets

# Percentage of the day's calorie target allocated to each slot.
# ASSUMPTION: a common, simple 5-meal distribution pattern. Documented here
# and in ASSUMPTIONS.md rather than invented silently.
MEAL_SLOT_CALORIE_SHARE = {
    "breakfast": 0.25,
    "mid_morning_snack": 0.10,
    "lunch": 0.30,
    "evening_snack": 0.10,
    "dinner": 0.25,
}

# Which foods.meal_type value each slot should draw candidates from.
MEAL_SLOT_TO_FOOD_MEAL_TYPE = {
    "breakfast": "breakfast",
    "mid_morning_snack": "snack",
    "lunch": "lunch",
    "evening_snack": "snack",
    "dinner": "dinner",
}


@dataclass
class MealPlanItemResult:
    meal_slot: str
    food: Optional[Food]
    reasons: List[str] = field(default_factory=list)


@dataclass
class MealPlanResult:
    items: List[MealPlanItemResult]
    target_calories: float
    target_protein_g: float
    total_calories: float
    total_protein_g: float
    calorie_difference: float
    protein_difference: float


def generate_daily_meal_plan(user_id: int) -> MealPlanResult:
    user = repo.get_user(user_id)
    if user is None:
        raise ValueError(f"No user found with id={user_id}")

    targets = repo.get_latest_nutrition_targets(user_id)
    if targets is None:
        raise ValueError("No nutrition targets found. Calculate the user's targets first.")

    allergies = repo.get_preference_values(user_id, "allergy")
    avoid_ingredients = repo.get_preference_values(user_id, "avoid_ingredient")
    disliked = repo.get_preference_values(user_id, "disliked_food")
    favorites = repo.get_preference_values(user_id, "favorite_food")
    exclude_allergens = allergies + avoid_ingredients

    used_food_names = set()
    items: List[MealPlanItemResult] = []
    total_calories = 0.0
    total_protein = 0.0

    for slot, share in MEAL_SLOT_CALORIE_SHARE.items():
        slot_calorie_budget = targets.calorie_target_kcal * share
        slot_protein_budget = targets.protein_target_g * share

        food_meal_type = MEAL_SLOT_TO_FOOD_MEAL_TYPE[slot]
        candidates = repo.search_foods(
            dietary_type=user.diet_type,
            meal_type=food_meal_type,
            exclude_allergens=exclude_allergens,
            exclude_names=list(disliked) + list(used_food_names),
            max_calories=slot_calorie_budget * 1.6,
        )

        if not candidates:
            items.append(MealPlanItemResult(meal_slot=slot, food=None,
                                             reasons=["No suitable food found for this slot under current constraints."]))
            continue

        scored = [
            score_food_for_remaining_targets(
                food, slot_calorie_budget, slot_protein_budget, favorites, user.cuisine_preference
            )
            for food in candidates
        ]
        scored.sort(key=lambda s: s.score, reverse=True)
        best = scored[0]

        items.append(MealPlanItemResult(meal_slot=slot, food=best.food, reasons=best.reasons))
        used_food_names.add(best.food.name)
        total_calories += best.food.calories
        total_protein += best.food.protein_g

    return MealPlanResult(
        items=items,
        target_calories=targets.calorie_target_kcal,
        target_protein_g=targets.protein_target_g,
        total_calories=round(total_calories, 1),
        total_protein_g=round(total_protein, 1),
        calorie_difference=round(total_calories - targets.calorie_target_kcal, 1),
        protein_difference=round(total_protein - targets.protein_target_g, 1),
    )
