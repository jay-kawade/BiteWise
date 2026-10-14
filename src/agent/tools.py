"""
tools.py
-------------------------------------------------------------------------------
The "hands" of the AI Nutrition Assistant (Section 17). These are plain
Python functions that wrap the application's existing, already-tested
modules (database, nutrition calculator, recommendation engine, scanner).

WHY THIS MATTERS (Section 17/18 -- agent safety):
The agent (whether it's the rule-based fallback in orchestrator.py, or a
real LLM using Anthropic's tool-use feature) is NEVER allowed to invent a
nutrition number, a food's calorie count, or a recommendation out of thin
air. It can only call these tools, which always go through the same
deterministic calculators / database / ML model used everywhere else in the
app. This keeps every number the assistant reports fully traceable and
consistent with the rest of the UI.

Every tool function:
    - takes plain, JSON-serializable arguments,
    - returns a plain, JSON-serializable dict,
    - never raises for "expected" situations (missing profile, empty
      search, etc.) -- it returns a dict with an "error" or "message" key
      instead, so the calling agent can react gracefully.
-------------------------------------------------------------------------------
"""

from dataclasses import asdict
from datetime import date, timedelta
from typing import Optional

from src.database import repositories as repo
from src.ml.predict import is_model_available, predict_meal_type
from src.nutrition.calculator import calculate_remaining_targets, compute_nutrition_targets, summarize_consumed
from src.recommendation.meal_planner import generate_daily_meal_plan
from src.recommendation.recommender import recommend_next_foods
from src.recommendation.substitution import find_food_by_name, find_substitutes
from src.scanner.scanner_service import scan_food_label


def get_user_profile(user_id: int) -> dict:
    user = repo.get_user(user_id)
    if not user:
        return {"error": f"No user profile found for user_id={user_id}."}
    profile = asdict(user)
    profile["allergies"] = repo.get_preference_values(user_id, "allergy")
    profile["avoid_ingredients"] = repo.get_preference_values(user_id, "avoid_ingredient")
    profile["favorite_foods"] = repo.get_preference_values(user_id, "favorite_food")
    profile["disliked_foods"] = repo.get_preference_values(user_id, "disliked_food")
    return profile


def get_daily_targets(user_id: int) -> dict:
    targets = repo.get_latest_nutrition_targets(user_id)
    if not targets:
        user = repo.get_user(user_id)
        if not user:
            return {"error": f"No user profile found for user_id={user_id}."}
        result = compute_nutrition_targets(user)
        return {
            "source": "calculated_now", "bmi": result.bmi, "bmi_category": result.bmi_category,
            "bmr_kcal": result.bmr_kcal, "tdee_kcal": result.tdee_kcal,
            "calorie_target_kcal": result.calorie_target_kcal, "protein_target_g": result.protein_target_g,
            "carb_target_g": result.carb_target_g, "fat_target_g": result.fat_target_g,
            "fiber_target_g": result.fiber_target_g,
        }
    return {"source": "stored", **{k: v for k, v in asdict(targets).items() if k not in ("id", "user_id")}}


def get_food_information(food_id: int) -> dict:
    food = repo.get_food(food_id)
    if not food:
        return {"error": f"No food found with id={food_id}."}
    return asdict(food)


def search_foods(query_text: str = "", dietary_type: Optional[str] = None,
                  meal_type: Optional[str] = None, max_calories: Optional[float] = None) -> dict:
    foods = repo.search_foods(query_text=query_text, dietary_type=dietary_type,
                               meal_type=meal_type, max_calories=max_calories)
    return {"count": len(foods), "foods": [asdict(f) for f in foods[:20]]}


def analyze_scanned_label(image_bytes: bytes, user_id: int) -> dict:
    remaining = get_remaining_targets_today(user_id)
    result = scan_food_label(
        image_bytes=image_bytes, user_id=user_id,
        remaining_calorie_budget=remaining.get("calories"),
        remaining_protein_budget=remaining.get("protein_g"),
    )
    output = {
        "ocr_mode": result.ocr_mode, "ocr_confidence": result.ocr_confidence,
        "parsed_nutrition": result.parsed_nutrition, "parsing_warnings": result.parsing_warnings,
        "ingredients": result.ingredients, "allergen_warnings": result.allergen_warnings,
        "allergen_disclaimer": result.allergen_disclaimer,
    }
    if result.suitability:
        output["suitability_label"] = result.suitability.suitability_label
        output["suitability_checklist"] = [f"{i.symbol} {i.text}" for i in result.suitability.checklist]
    if result.parsed_nutrition and is_model_available():
        prediction = predict_meal_type(
            result.parsed_nutrition,
            serving_size_g=result.parsed_nutrition.get("serving_size_g", 100.0),
        )
        if prediction:
            output["ml_predicted_meal_type"] = prediction.predicted_meal_type
            output["ml_confidence"] = prediction.confidence
    return output


def check_ingredients(ingredients: list, user_id: int) -> dict:
    from src.scanner.ingredient_parser import check_allergens_and_restrictions
    allergies = repo.get_preference_values(user_id, "allergy")
    avoid = repo.get_preference_values(user_id, "avoid_ingredient")
    result = check_allergens_and_restrictions(ingredients, allergies, avoid)
    return {
        "detected_allergens": result.detected_allergens,
        "warnings": [f"{w.allergen_or_term} (matched \"{w.matched_ingredient_text}\")" for w in result.warnings],
    }


def log_food(user_id: int, food_name: str, meal_type: str, quantity_servings: float = 1.0,
             food_id: Optional[int] = None, nutrition: Optional[dict] = None) -> dict:
    from src.database.models import FoodLogEntry

    if food_id:
        food = repo.get_food(food_id)
        if not food:
            return {"error": f"No food found with id={food_id}."}
        calories = food.calories * quantity_servings
        protein_g = food.protein_g * quantity_servings
        carbs_g = food.carbohydrates_g * quantity_servings
        fat_g = food.fat_g * quantity_servings
        fiber_g = food.fiber_g * quantity_servings
        sugar_g = food.sugar_g * quantity_servings
        sodium_mg = food.sodium_mg * quantity_servings
        source = "database"
    elif nutrition:
        calories = nutrition.get("calories", 0.0) * quantity_servings
        protein_g = nutrition.get("protein_g", 0.0) * quantity_servings
        carbs_g = nutrition.get("carbohydrates_g", 0.0) * quantity_servings
        fat_g = nutrition.get("fat_g", 0.0) * quantity_servings
        fiber_g = nutrition.get("fiber_g", 0.0) * quantity_servings
        sugar_g = nutrition.get("sugar_g", 0.0) * quantity_servings
        sodium_mg = nutrition.get("sodium_mg", 0.0) * quantity_servings
        source = "scanned"
    else:
        return {"error": "Either food_id or nutrition values must be provided to log a food."}

    entry = FoodLogEntry(
        id=None, user_id=user_id, food_id=food_id, food_name=food_name, meal_type=meal_type,
        quantity_servings=quantity_servings, calories=calories, protein_g=protein_g,
        carbohydrates_g=carbs_g, fat_g=fat_g, fiber_g=fiber_g, sugar_g=sugar_g, sodium_mg=sodium_mg,
        log_source=source,
    )
    log_id = repo.log_food(entry)
    return {"log_id": log_id, "logged": {"food_name": food_name, "calories": round(calories, 1), "protein_g": round(protein_g, 1)}}


def get_daily_consumption(user_id: int, log_date: Optional[str] = None) -> dict:
    entries = repo.get_food_logs_for_date(user_id, log_date)
    totals = summarize_consumed(entries)
    return {"log_date": log_date or str(date.today()), "entries_count": len(entries), "totals": totals}


def get_remaining_targets_today(user_id: int) -> dict:
    targets_row = repo.get_latest_nutrition_targets(user_id)
    if not targets_row:
        return {}
    consumption = get_daily_consumption(user_id)

    class _T:
        pass
    t = _T()
    t.calorie_target_kcal = targets_row.calorie_target_kcal
    t.protein_target_g = targets_row.protein_target_g
    t.carb_target_g = targets_row.carb_target_g
    t.fat_target_g = targets_row.fat_target_g
    t.fiber_target_g = targets_row.fiber_target_g

    return calculate_remaining_targets(t, consumption["totals"])


def generate_meal_plan(user_id: int) -> dict:
    try:
        plan = generate_daily_meal_plan(user_id)
    except ValueError as exc:
        return {"error": str(exc)}
    return {
        "target_calories": plan.target_calories, "target_protein_g": plan.target_protein_g,
        "total_calories": plan.total_calories, "total_protein_g": plan.total_protein_g,
        "calorie_difference": plan.calorie_difference, "protein_difference": plan.protein_difference,
        "items": [
            {"meal_slot": i.meal_slot, "food_name": i.food.name if i.food else None, "reasons": i.reasons}
            for i in plan.items
        ],
    }


def suggest_substitutions(user_id: int, food_name: str) -> dict:
    original = find_food_by_name(food_name)
    if not original:
        return {"error": f"Could not find '{food_name}' in the food database."}
    substitutes = find_substitutes(original, user_id)
    return {
        "original_food": original.name,
        "substitutes": [
            {"name": s.food.name, "score": s.score, "reasons": s.reasons} for s in substitutes
        ],
    }


def suggest_next_foods(user_id: int, meal_type: Optional[str] = None, top_n: int = 5) -> dict:
    user = repo.get_user(user_id)
    if not user:
        return {"error": f"No user profile found for user_id={user_id}."}
    remaining = get_remaining_targets_today(user_id)
    if not remaining:
        return {"error": "No nutrition targets found. Calculate targets first."}
    results = recommend_next_foods(
        user_id, remaining_calories=remaining["calories"], remaining_protein_g=remaining["protein_g"],
        diet_type=user.diet_type, meal_type=meal_type, top_n=top_n,
    )
    return {
        "remaining_calories": remaining["calories"], "remaining_protein_g": remaining["protein_g"],
        "recommendations": [{"name": s.food.name, "score": s.score, "reasons": s.reasons} for s in results],
    }


def get_weekly_summary(user_id: int) -> dict:
    end = date.today()
    start = end - timedelta(days=6)
    entries = repo.get_food_logs_between(user_id, str(start), str(end))
    if not entries:
        return {"message": "No logged foods in the last 7 days.", "days_logged": 0}

    by_date: dict = {}
    for e in entries:
        by_date.setdefault(e.log_date, []).append(e)

    daily_totals = {d: summarize_consumed(es) for d, es in by_date.items()}
    n_days = len(daily_totals)
    avg = {
        key: round(sum(day[key] for day in daily_totals.values()) / n_days, 1)
        for key in ["calories", "protein_g", "carbohydrates_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg"]
    }

    targets = repo.get_latest_nutrition_targets(user_id)
    days_below_protein_target = 0
    if targets:
        days_below_protein_target = sum(1 for day in daily_totals.values() if day["protein_g"] < targets.protein_target_g)

    return {
        "date_range": f"{start} to {end}", "days_logged": n_days,
        "average_daily": avg, "days_below_protein_target": days_below_protein_target,
        "total_meals_logged": len(entries),
    }
