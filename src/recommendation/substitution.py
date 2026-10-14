"""
substitution.py
-------------------------------------------------------------------------------
Implements Section 14: "Smart Food Substitution".

Given a food the user wants to replace, this finds nutritionally similar
alternatives from the database that also respect the user's dietary type,
allergies, and ingredients to avoid.
-------------------------------------------------------------------------------
"""

from typing import List, Optional

from src.database import repositories as repo
from src.database.models import Food
from src.recommendation.ranking import ScoredFood, score_substitution


def find_substitutes(
    original_food: Food,
    user_id: int,
    top_n: int = 5,
) -> List[ScoredFood]:
    user = repo.get_user(user_id)
    diet_type = user.diet_type if user else None
    allergies = repo.get_preference_values(user_id, "allergy")
    avoid_ingredients = repo.get_preference_values(user_id, "avoid_ingredient")

    candidates = repo.search_foods(
        dietary_type=diet_type,
        exclude_allergens=allergies + avoid_ingredients,
        exclude_names=[original_food.name],
    )

    if not candidates:
        return []

    scored = [score_substitution(original_food, candidate) for candidate in candidates]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored[:top_n]


def find_food_by_name(name: str) -> Optional[Food]:
    matches = repo.search_foods(query_text=name)
    for food in matches:
        if food.name.lower() == name.lower():
            return food
    return matches[0] if matches else None
