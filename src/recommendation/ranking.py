"""
ranking.py
-------------------------------------------------------------------------------
The scoring/ranking functions used by the recommendation engine. Everything
here is a TRANSPARENT, explainable formula (weighted distances) -- not a
trained/black-box model. This is intentional (Section 5 requires the app to
clearly separate ML predictions from rule-based/ranking logic), and it means
every recommendation can be explained in one sentence during a viva.

All weights are named constants below so they are easy to find and tune.
-------------------------------------------------------------------------------
"""

import math
from dataclasses import dataclass
from typing import Dict, List

from src.database.models import Food

# ------------------------------------------------------------------
# Weights for "what should I eat next" ranking. They must sum to 1.0 to
# keep the resulting score in an intuitive 0-1-ish range, but this is not a
# strict requirement of the math -- just a readability convention.
# ------------------------------------------------------------------
NEXT_MEAL_WEIGHTS = {
    "calorie_fit": 0.30,     # how close the food's calories are to the remaining budget without exceeding it much
    "protein_fit": 0.35,     # how well the food helps close the remaining protein gap
    "macro_balance": 0.15,   # rewards foods with fiber and without excessive sugar/sodium
    "preference_bonus": 0.20,  # favorite foods / preferred cuisine get a boost
}

# ------------------------------------------------------------------
# Weights for substitution ranking (Section 14).
# ------------------------------------------------------------------
SUBSTITUTION_WEIGHTS = {
    "protein_similarity": 0.35,
    "calorie_similarity": 0.30,
    "macro_similarity": 0.20,
    "meal_compatibility": 0.15,
}


def _closeness_score(value: float, target: float, tolerance: float) -> float:
    """
    Returns 1.0 when value == target, decaying smoothly to 0.0 as the
    absolute difference grows past `tolerance`. Used to reward foods whose
    calories/protein are "close to" a target/remaining amount rather than
    requiring an exact match (which would almost never happen).
    """
    if target <= 0:
        return 0.5  # no meaningful target to compare against
    diff = abs(value - target)
    return max(0.0, 1.0 - (diff / max(tolerance, 1e-6)))


@dataclass
class ScoredFood:
    food: Food
    score: float
    reasons: List[str]


def score_food_for_remaining_targets(
    food: Food,
    remaining_calories: float,
    remaining_protein_g: float,
    favorite_foods: List[str],
    preferred_cuisine: str,
    weights: Dict[str, float] = None,
) -> ScoredFood:
    """
    Score one candidate food against how well it fits the user's REMAINING
    daily nutrition targets (Section 12, "What should I eat next?").
    """
    weights = weights or NEXT_MEAL_WEIGHTS
    reasons = []

    # Calorie fit: reward foods that use up a reasonable chunk of the
    # remaining budget without blowing far past it. Tolerance scales with
    # the remaining budget itself.
    calorie_tolerance = max(remaining_calories * 0.6, 150)
    calorie_score = _closeness_score(food.calories, min(food.calories, remaining_calories), calorie_tolerance) \
        if food.calories <= remaining_calories * 1.3 else 0.2
    if food.calories <= remaining_calories:
        reasons.append(f"Fits within your remaining {remaining_calories:.0f} kcal budget")
    else:
        reasons.append("Slightly exceeds your remaining calorie budget")

    # Protein fit: reward foods that help close the protein gap.
    protein_tolerance = max(remaining_protein_g * 0.6, 10)
    protein_score = _closeness_score(food.protein_g, min(food.protein_g, remaining_protein_g), protein_tolerance)
    if food.protein_g >= remaining_protein_g * 0.3 and remaining_protein_g > 0:
        reasons.append(f"Provides {food.protein_g:.0f}g protein toward your remaining {remaining_protein_g:.0f}g target")

    # Macro balance: reward fiber, mildly penalize very high sugar/sodium per 100g.
    scale = 100.0 / food.serving_size_g if food.serving_size_g else 1.0
    fiber_100g = food.fiber_g * scale
    sugar_100g = food.sugar_g * scale
    sodium_100g = food.sodium_mg * scale
    balance_score = 0.5
    balance_score += 0.25 if fiber_100g >= 3 else 0.0
    balance_score -= 0.2 if sugar_100g >= 15 else 0.0
    balance_score -= 0.2 if sodium_100g >= 400 else 0.0
    balance_score = min(max(balance_score, 0.0), 1.0)
    if fiber_100g >= 3:
        reasons.append("Good source of fiber")
    if sugar_100g >= 15:
        reasons.append("Note: relatively high in sugar")
    if sodium_100g >= 400:
        reasons.append("Note: relatively high in sodium")

    # Preference bonus.
    preference_score = 0.0
    name_lower = food.name.lower()
    if any(fav.lower() in name_lower or name_lower in fav.lower() for fav in favorite_foods):
        preference_score += 0.7
        reasons.append("One of your favorite foods")
    if preferred_cuisine and food.cuisine.lower() == preferred_cuisine.lower():
        preference_score += 0.3
        reasons.append(f"Matches your preferred {preferred_cuisine} cuisine")
    preference_score = min(preference_score, 1.0)

    total_score = (
        weights["calorie_fit"] * calorie_score
        + weights["protein_fit"] * protein_score
        + weights["macro_balance"] * balance_score
        + weights["preference_bonus"] * preference_score
    )

    return ScoredFood(food=food, score=round(total_score, 4), reasons=reasons)


# Reference scales used to standardize each nutrient before computing cosine
# similarity. WHY THIS MATTERS: calories (~50-500) is numerically much larger
# than protein/fat/fiber (~0-30), so an un-standardized vector's *direction*
# is dominated almost entirely by calories -- nearly every calorie-dense food
# then looks "similar" to every other one, regardless of whether it is a
# protein source or a carb source. Dividing each nutrient by a typical value
# (chosen so all features land in a comparable ~0-5 range) makes the cosine
# angle actually reflect the food's macro *composition*, which is what a
# substitution should match.
_REFERENCE_SCALE = {
    "calories": 50.0, "protein_g": 10.0, "carbs_g": 20.0,
    "fat_g": 10.0, "fiber_g": 5.0, "sugar_g": 10.0, "sodium_mg": 200.0,
}


def _nutrient_vector_per_100g(food: Food) -> List[float]:
    scale = 100.0 / food.serving_size_g if food.serving_size_g else 1.0
    return [
        (food.calories * scale) / _REFERENCE_SCALE["calories"],
        (food.protein_g * scale) / _REFERENCE_SCALE["protein_g"],
        (food.carbohydrates_g * scale) / _REFERENCE_SCALE["carbs_g"],
        (food.fat_g * scale) / _REFERENCE_SCALE["fat_g"],
        (food.fiber_g * scale) / _REFERENCE_SCALE["fiber_g"],
        (food.sugar_g * scale) / _REFERENCE_SCALE["sugar_g"],
        (food.sodium_mg * scale) / _REFERENCE_SCALE["sodium_mg"],
    ]


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def score_substitution(original: Food, candidate: Food, weights: Dict[str, float] = None) -> ScoredFood:
    """
    Rank a candidate replacement food by nutrient-profile similarity to the
    original food, using per-100g normalized vectors and cosine similarity
    (Section 14: "Smart Food Substitution").
    """
    weights = weights or SUBSTITUTION_WEIGHTS
    reasons = []

    scale_o = 100.0 / original.serving_size_g if original.serving_size_g else 1.0
    scale_c = 100.0 / candidate.serving_size_g if candidate.serving_size_g else 1.0

    protein_similarity = 1.0 - min(abs(original.protein_g * scale_o - candidate.protein_g * scale_c) / 30.0, 1.0)
    calorie_similarity = 1.0 - min(abs(original.calories * scale_o - candidate.calories * scale_c) / 300.0, 1.0)

    macro_similarity = cosine_similarity(
        _nutrient_vector_per_100g(original), _nutrient_vector_per_100g(candidate)
    )

    meal_compatibility = 1.0 if original.meal_type == candidate.meal_type else 0.4

    if protein_similarity > 0.7:
        reasons.append("Similar protein content")
    if calorie_similarity > 0.7:
        reasons.append("Similar calorie content")
    if meal_compatibility == 1.0:
        reasons.append(f"Commonly eaten at the same meal ({candidate.meal_type})")
    reasons.append(f"Overall nutrient profile similarity: {macro_similarity:.0%}")

    total_score = (
        weights["protein_similarity"] * protein_similarity
        + weights["calorie_similarity"] * calorie_similarity
        + weights["macro_similarity"] * macro_similarity
        + weights["meal_compatibility"] * meal_compatibility
    )

    return ScoredFood(food=candidate, score=round(total_score, 4), reasons=reasons)
