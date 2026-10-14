"""
validation.py
-------------------------------------------------------------------------------
Input validation for anything that goes into the nutrition calculator or the
user profile form. Keeping this separate from formulas.py means the "what is
a valid input" question is answered in exactly one place.

Every function returns a list of human-readable error strings. An empty list
means the input is valid. This pattern (instead of raising exceptions for
expected user-input problems) makes it easy for the Streamlit UI to show all
problems to the user at once.
-------------------------------------------------------------------------------
"""

from typing import List

# Reasonable real-world bounds. These are sanity limits, not medical cutoffs.
MIN_AGE, MAX_AGE = 10, 100
MIN_HEIGHT_CM, MAX_HEIGHT_CM = 100.0, 250.0
MIN_WEIGHT_KG, MAX_WEIGHT_KG = 25.0, 300.0
MIN_SLEEP_HOURS, MAX_SLEEP_HOURS = 0.0, 16.0
VALID_SEX = {"male", "female", "other"}
VALID_ACTIVITY_LEVELS = {"sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"}
VALID_GOALS = {"weight_loss", "maintenance", "weight_gain", "muscle_gain"}
VALID_DIET_TYPES = {"vegan", "vegetarian", "eggetarian", "non_vegetarian"}


def validate_profile_inputs(
    name: str,
    age: int,
    sex: str,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    goal: str,
    diet_type: str,
    sleep_hours: float = 7.0,
) -> List[str]:
    errors: List[str] = []

    if not name or not name.strip():
        errors.append("Name cannot be empty.")

    if not isinstance(age, (int, float)) or age < MIN_AGE or age > MAX_AGE:
        errors.append(f"Age must be between {MIN_AGE} and {MAX_AGE} years.")

    if sex not in VALID_SEX:
        errors.append(f"Sex must be one of: {', '.join(sorted(VALID_SEX))}.")

    if not isinstance(height_cm, (int, float)) or height_cm < MIN_HEIGHT_CM or height_cm > MAX_HEIGHT_CM:
        errors.append(f"Height must be between {MIN_HEIGHT_CM} and {MAX_HEIGHT_CM} cm.")

    if not isinstance(weight_kg, (int, float)) or weight_kg < MIN_WEIGHT_KG or weight_kg > MAX_WEIGHT_KG:
        errors.append(f"Weight must be between {MIN_WEIGHT_KG} and {MAX_WEIGHT_KG} kg.")

    if activity_level not in VALID_ACTIVITY_LEVELS:
        errors.append(f"Activity level must be one of: {', '.join(sorted(VALID_ACTIVITY_LEVELS))}.")

    if goal not in VALID_GOALS:
        errors.append(f"Goal must be one of: {', '.join(sorted(VALID_GOALS))}.")

    if diet_type not in VALID_DIET_TYPES:
        errors.append(f"Diet type must be one of: {', '.join(sorted(VALID_DIET_TYPES))}.")

    if not isinstance(sleep_hours, (int, float)) or sleep_hours < MIN_SLEEP_HOURS or sleep_hours > MAX_SLEEP_HOURS:
        errors.append(f"Sleep hours must be between {MIN_SLEEP_HOURS} and {MAX_SLEEP_HOURS}.")

    return errors


def validate_food_log_quantity(quantity_servings: float) -> List[str]:
    errors = []
    if not isinstance(quantity_servings, (int, float)) or quantity_servings <= 0:
        errors.append("Quantity (servings) must be a positive number.")
    if isinstance(quantity_servings, (int, float)) and quantity_servings > 20:
        errors.append("Quantity looks unusually large (more than 20 servings). Please double-check.")
    return errors
