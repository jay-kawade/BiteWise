"""
recommender.py
-------------------------------------------------------------------------------
Implements Section 12: "What should I eat next?"

Given a user's profile, remaining nutrition targets, and constraints
(dietary type, allergies, disliked foods, meal type), this searches the food
database and ranks candidates using the transparent weighted-scoring
function in ranking.py.
-------------------------------------------------------------------------------
"""

from typing import List, Optional

from src.database import repositories as repo
from src.recommendation.ranking import ScoredFood, score_food_for_remaining_targets


def recommend_next_foods(
    user_id: int,
    remaining_calories: float,
    remaining_protein_g: float,
    diet_type: str,
    meal_type: Optional[str] = None,
    top_n: int = 5,
) -> List[ScoredFood]:
    """
    Returns the top_n foods that best fit the user's remaining nutrition
    targets and constraints, most-suitable first.
    """
    allergies = repo.get_preference_values(user_id, "allergy")
    avoid_ingredients = repo.get_preference_values(user_id, "avoid_ingredient")
    disliked = repo.get_preference_values(user_id, "disliked_food")
    favorites = repo.get_preference_values(user_id, "favorite_food")

    user = repo.get_user(user_id)
    preferred_cuisine = user.cuisine_preference if user else ""

    exclude_allergens = allergies + avoid_ingredients

    candidates = repo.search_foods(
        dietary_type=diet_type,
        meal_type=meal_type,
        exclude_allergens=exclude_allergens,
        exclude_names=disliked,
        max_calories=max(remaining_calories * 1.3, 100),  # don't suggest something wildly over budget
    )

    if not candidates:
        return []

    scored = [
        score_food_for_remaining_targets(
            food, remaining_calories, remaining_protein_g, favorites, preferred_cuisine
        )
        for food in candidates
    ]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored[:top_n]


def search_foods_for_user(
    user_id: int,
    query_text: str = "",
    meal_type: Optional[str] = None,
):
    """A simple, explainable search used by the Food Log / Recommendations pages."""
    user = repo.get_user(user_id)
    diet_type = user.diet_type if user else None
    allergies = repo.get_preference_values(user_id, "allergy")
    avoid_ingredients = repo.get_preference_values(user_id, "avoid_ingredient")

    return repo.search_foods(
        query_text=query_text,
        dietary_type=diet_type,
        meal_type=meal_type,
        exclude_allergens=allergies + avoid_ingredients,
    )
