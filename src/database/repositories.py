"""
repositories.py
-------------------------------------------------------------------------------
This module is the ONLY place in the application that writes raw SQL. Every
other module (nutrition engine, recommender, scanner, agent, UI pages) should
call functions from here instead of touching sqlite3 directly.

Why this matters: if we ever swap SQLite for something else, or plug in a
real external food-data API, only this file needs to change.
-------------------------------------------------------------------------------
"""

import json
from datetime import date
from typing import List, Optional

from src.database.db import get_cursor
from src.database.models import (
    Food,
    FoodLogEntry,
    MealPlan,
    MealPlanItem,
    NutritionTargets,
    ScannedFood,
    UserPreference,
    UserProfile,
)

# ==============================================================================
# USERS
# ==============================================================================

def create_user(profile: UserProfile) -> int:
    """Insert a new user profile and return its new id."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO users (
                name, age, sex, height_cm, weight_kg, activity_level,
                exercise_frequency_per_week, exercise_type, sleep_hours, goal,
                diet_type, cuisine_preference, budget_preference,
                cooking_time_preference, meals_per_day, health_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile.name, profile.age, profile.sex, profile.height_cm,
                profile.weight_kg, profile.activity_level,
                profile.exercise_frequency_per_week, profile.exercise_type,
                profile.sleep_hours, profile.goal, profile.diet_type,
                profile.cuisine_preference, profile.budget_preference,
                profile.cooking_time_preference, profile.meals_per_day,
                profile.health_notes,
            ),
        )
        return cur.lastrowid


def update_user(profile: UserProfile) -> None:
    """Update an existing user profile (profile.id must be set)."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE users SET
                name = ?, age = ?, sex = ?, height_cm = ?, weight_kg = ?,
                activity_level = ?, exercise_frequency_per_week = ?,
                exercise_type = ?, sleep_hours = ?, goal = ?, diet_type = ?,
                cuisine_preference = ?, budget_preference = ?,
                cooking_time_preference = ?, meals_per_day = ?,
                health_notes = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                profile.name, profile.age, profile.sex, profile.height_cm,
                profile.weight_kg, profile.activity_level,
                profile.exercise_frequency_per_week, profile.exercise_type,
                profile.sleep_hours, profile.goal, profile.diet_type,
                profile.cuisine_preference, profile.budget_preference,
                profile.cooking_time_preference, profile.meals_per_day,
                profile.health_notes, profile.id,
            ),
        )


def get_user(user_id: int) -> Optional[UserProfile]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        return _row_to_user(row) if row else None


def list_users() -> List[UserProfile]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM users ORDER BY id")
        return [_row_to_user(r) for r in cur.fetchall()]


def _row_to_user(row) -> UserProfile:
    return UserProfile(
        id=row["id"], name=row["name"], age=row["age"], sex=row["sex"],
        height_cm=row["height_cm"], weight_kg=row["weight_kg"],
        activity_level=row["activity_level"],
        exercise_frequency_per_week=row["exercise_frequency_per_week"],
        exercise_type=row["exercise_type"] or "", sleep_hours=row["sleep_hours"],
        goal=row["goal"], diet_type=row["diet_type"],
        cuisine_preference=row["cuisine_preference"] or "indian",
        budget_preference=row["budget_preference"] or "medium",
        cooking_time_preference=row["cooking_time_preference"] or "medium",
        meals_per_day=row["meals_per_day"], health_notes=row["health_notes"] or "",
    )


# ==============================================================================
# USER PREFERENCES (favorites, dislikes, allergies, ingredients to avoid)
# ==============================================================================

def set_user_preferences(user_id: int, preference_type: str, values: List[str]) -> None:
    """Replace all preferences of one type (e.g. all 'allergy' rows) for a user."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM user_preferences WHERE user_id = ? AND preference_type = ?",
            (user_id, preference_type),
        )
        for value in values:
            value = value.strip()
            if value:
                cur.execute(
                    "INSERT INTO user_preferences (user_id, preference_type, value) VALUES (?, ?, ?)",
                    (user_id, preference_type, value),
                )


def get_user_preferences(user_id: int, preference_type: Optional[str] = None) -> List[UserPreference]:
    with get_cursor() as cur:
        if preference_type:
            cur.execute(
                "SELECT * FROM user_preferences WHERE user_id = ? AND preference_type = ?",
                (user_id, preference_type),
            )
        else:
            cur.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
        return [
            UserPreference(id=r["id"], user_id=r["user_id"],
                            preference_type=r["preference_type"], value=r["value"])
            for r in cur.fetchall()
        ]


def get_preference_values(user_id: int, preference_type: str) -> List[str]:
    return [p.value for p in get_user_preferences(user_id, preference_type)]


# ==============================================================================
# NUTRITION TARGETS
# ==============================================================================

def save_nutrition_targets(targets: NutritionTargets) -> int:
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO nutrition_targets (
                user_id, bmi, bmi_category, bmr_kcal, tdee_kcal,
                calorie_target_kcal, protein_target_g, carb_target_g,
                fat_target_g, fiber_target_g
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                targets.user_id, targets.bmi, targets.bmi_category,
                targets.bmr_kcal, targets.tdee_kcal, targets.calorie_target_kcal,
                targets.protein_target_g, targets.carb_target_g,
                targets.fat_target_g, targets.fiber_target_g,
            ),
        )
        return cur.lastrowid


def get_latest_nutrition_targets(user_id: int) -> Optional[NutritionTargets]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM nutrition_targets WHERE user_id = ? ORDER BY calculated_at DESC LIMIT 1",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return NutritionTargets(
            id=row["id"], user_id=row["user_id"], bmi=row["bmi"],
            bmi_category=row["bmi_category"], bmr_kcal=row["bmr_kcal"],
            tdee_kcal=row["tdee_kcal"], calorie_target_kcal=row["calorie_target_kcal"],
            protein_target_g=row["protein_target_g"], carb_target_g=row["carb_target_g"],
            fat_target_g=row["fat_target_g"], fiber_target_g=row["fiber_target_g"],
            calculated_at=row["calculated_at"],
        )


# ==============================================================================
# FOODS
# ==============================================================================

def _row_to_food(row) -> Food:
    return Food(
        id=row["id"], name=row["name"], category=row["category"],
        serving_size_g=row["serving_size_g"], calories=row["calories"],
        protein_g=row["protein_g"], carbohydrates_g=row["carbohydrates_g"],
        fat_g=row["fat_g"], fiber_g=row["fiber_g"], sugar_g=row["sugar_g"],
        sodium_mg=row["sodium_mg"], saturated_fat_g=row["saturated_fat_g"],
        dietary_type=row["dietary_type"], meal_type=row["meal_type"],
        cuisine=row["cuisine"] or "other", allergens=row["allergens"] or "",
        tags=row["tags"] or "", source=row["source"],
    )


def insert_food(food: Food) -> int:
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO foods (
                name, category, serving_size_g, calories, protein_g,
                carbohydrates_g, fat_g, fiber_g, sugar_g, sodium_mg,
                saturated_fat_g, dietary_type, meal_type, cuisine, allergens,
                tags, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                food.name, food.category, food.serving_size_g, food.calories,
                food.protein_g, food.carbohydrates_g, food.fat_g, food.fiber_g,
                food.sugar_g, food.sodium_mg, food.saturated_fat_g,
                food.dietary_type, food.meal_type, food.cuisine, food.allergens,
                food.tags, food.source,
            ),
        )
        return cur.lastrowid


def get_food(food_id: int) -> Optional[Food]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM foods WHERE id = ?", (food_id,))
        row = cur.fetchone()
        return _row_to_food(row) if row else None


def count_foods() -> int:
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM foods")
        return cur.fetchone()["n"]


def list_all_foods() -> List[Food]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM foods ORDER BY name")
        return [_row_to_food(r) for r in cur.fetchall()]


def search_foods(
    query_text: str = "",
    dietary_type: Optional[str] = None,
    meal_type: Optional[str] = None,
    exclude_allergens: Optional[List[str]] = None,
    exclude_names: Optional[List[str]] = None,
    max_calories: Optional[float] = None,
) -> List[Food]:
    """
    Search the food database with optional filters. This is deliberately a
    plain, readable filter function (not a black-box ML search) so its
    behaviour can be explained clearly in a viva.
    """
    sql = "SELECT * FROM foods WHERE 1=1"
    params: list = []

    if query_text:
        sql += " AND LOWER(name) LIKE ?"
        params.append(f"%{query_text.lower()}%")

    if dietary_type:
        # A stricter diet is always compatible with foods for a looser one,
        # e.g. a vegan user can eat "vegan" foods only, but a
        # "non_vegetarian" user can eat foods of any dietary_type.
        allowed = _compatible_dietary_types(dietary_type)
        placeholders = ",".join("?" for _ in allowed)
        sql += f" AND dietary_type IN ({placeholders})"
        params.extend(allowed)

    if meal_type:
        sql += " AND meal_type = ?"
        params.append(meal_type)

    if max_calories is not None:
        sql += " AND calories <= ?"
        params.append(max_calories)

    sql += " ORDER BY name"

    with get_cursor() as cur:
        cur.execute(sql, params)
        foods = [_row_to_food(r) for r in cur.fetchall()]

    if exclude_allergens:
        exclude_allergens_lower = {a.strip().lower() for a in exclude_allergens if a.strip()}
        foods = [f for f in foods if not (exclude_allergens_lower & {a.lower() for a in f.allergen_list()})]

    if exclude_names:
        exclude_lower = {n.strip().lower() for n in exclude_names if n.strip()}
        foods = [f for f in foods if f.name.strip().lower() not in exclude_lower]

    return foods


def _compatible_dietary_types(user_diet_type: str) -> List[str]:
    """
    Returns which food dietary_types a user with a given diet can eat.
    vegan       -> only vegan foods
    vegetarian  -> vegan + vegetarian foods
    eggetarian  -> vegan + vegetarian + eggetarian foods
    non_vegetarian -> all foods
    """
    hierarchy = ["vegan", "vegetarian", "eggetarian", "non_vegetarian"]
    if user_diet_type not in hierarchy:
        return hierarchy
    cutoff = hierarchy.index(user_diet_type)
    return hierarchy[: cutoff + 1]


# ==============================================================================
# FOOD LOGS (daily tracker)
# ==============================================================================

def log_food(entry: FoodLogEntry, log_date: Optional[str] = None) -> int:
    log_date = log_date or str(date.today())
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO food_logs (
                user_id, food_id, food_name, meal_type, quantity_servings,
                calories, protein_g, carbohydrates_g, fat_g, fiber_g,
                sugar_g, sodium_mg, log_source, log_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.user_id, entry.food_id, entry.food_name, entry.meal_type,
                entry.quantity_servings, entry.calories, entry.protein_g,
                entry.carbohydrates_g, entry.fat_g, entry.fiber_g,
                entry.sugar_g, entry.sodium_mg, entry.log_source, log_date,
            ),
        )
        return cur.lastrowid


def get_food_logs_for_date(user_id: int, log_date: Optional[str] = None) -> List[FoodLogEntry]:
    log_date = log_date or str(date.today())
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM food_logs WHERE user_id = ? AND log_date = ? ORDER BY logged_at",
            (user_id, log_date),
        )
        return [_row_to_log(r) for r in cur.fetchall()]


def get_food_logs_between(user_id: int, start_date: str, end_date: str) -> List[FoodLogEntry]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM food_logs
            WHERE user_id = ? AND log_date BETWEEN ? AND ?
            ORDER BY log_date, logged_at
            """,
            (user_id, start_date, end_date),
        )
        return [_row_to_log(r) for r in cur.fetchall()]


def delete_food_log(log_id: int) -> None:
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM food_logs WHERE id = ?", (log_id,))


def _row_to_log(row) -> FoodLogEntry:
    return FoodLogEntry(
        id=row["id"], user_id=row["user_id"], food_id=row["food_id"],
        food_name=row["food_name"], meal_type=row["meal_type"],
        quantity_servings=row["quantity_servings"], calories=row["calories"],
        protein_g=row["protein_g"], carbohydrates_g=row["carbohydrates_g"],
        fat_g=row["fat_g"], fiber_g=row["fiber_g"], sugar_g=row["sugar_g"],
        sodium_mg=row["sodium_mg"], log_source=row["log_source"],
        logged_at=row["logged_at"], log_date=row["log_date"],
    )


# ==============================================================================
# SCANNED FOODS
# ==============================================================================

def save_scanned_food(scanned: ScannedFood) -> int:
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO scanned_foods (
                user_id, raw_ocr_text, parsed_nutrition_json,
                parsed_ingredients_json, allergen_warnings_json,
                confidence_score, ocr_mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scanned.user_id, scanned.raw_ocr_text,
                json.dumps(scanned.parsed_nutrition),
                json.dumps(scanned.parsed_ingredients),
                json.dumps(scanned.allergen_warnings),
                scanned.confidence_score, scanned.ocr_mode,
            ),
        )
        return cur.lastrowid


def get_recent_scans(user_id: int, limit: int = 10) -> List[ScannedFood]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM scanned_foods WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        results = []
        for r in cur.fetchall():
            results.append(ScannedFood(
                id=r["id"], user_id=r["user_id"], raw_ocr_text=r["raw_ocr_text"],
                parsed_nutrition=json.loads(r["parsed_nutrition_json"]),
                parsed_ingredients=json.loads(r["parsed_ingredients_json"]),
                allergen_warnings=json.loads(r["allergen_warnings_json"]),
                confidence_score=r["confidence_score"], ocr_mode=r["ocr_mode"],
                created_at=r["created_at"],
            ))
        return results


# ==============================================================================
# MEAL PLANS
# ==============================================================================

def save_meal_plan(plan: MealPlan) -> int:
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO meal_plans (
                user_id, plan_date, plan_type, target_calories,
                target_protein_g, total_calories, total_protein_g
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan.user_id, plan.plan_date, plan.plan_type, plan.target_calories,
                plan.target_protein_g, plan.total_calories, plan.total_protein_g,
            ),
        )
        plan_id = cur.lastrowid
        for item in plan.items:
            cur.execute(
                """
                INSERT INTO meal_plan_items (meal_plan_id, meal_slot, food_id, food_name, quantity_servings)
                VALUES (?, ?, ?, ?, ?)
                """,
                (plan_id, item.meal_slot, item.food_id, item.food_name, item.quantity_servings),
            )
        return plan_id


def get_latest_meal_plan(user_id: int, plan_type: str = "daily") -> Optional[MealPlan]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM meal_plans WHERE user_id = ? AND plan_type = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (user_id, plan_type),
        )
        row = cur.fetchone()
        if not row:
            return None
        cur.execute("SELECT * FROM meal_plan_items WHERE meal_plan_id = ?", (row["id"],))
        items = [
            MealPlanItem(id=i["id"], meal_plan_id=i["meal_plan_id"], meal_slot=i["meal_slot"],
                         food_id=i["food_id"], food_name=i["food_name"],
                         quantity_servings=i["quantity_servings"])
            for i in cur.fetchall()
        ]
        return MealPlan(
            id=row["id"], user_id=row["user_id"], plan_date=row["plan_date"],
            plan_type=row["plan_type"], target_calories=row["target_calories"],
            target_protein_g=row["target_protein_g"], total_calories=row["total_calories"],
            total_protein_g=row["total_protein_g"], items=items,
        )


# ==============================================================================
# RECOMMENDATIONS & FEEDBACK
# ==============================================================================

def log_recommendation(user_id: int, context: str, food_id: Optional[int],
                        food_name: str, score: float, reason: str) -> int:
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO recommendations (user_id, context, food_id, food_name, score, reason)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, context, food_id, food_name, score, reason),
        )
        return cur.lastrowid


def save_feedback(user_id: int, recommendation_id: Optional[int], rating: int, comment: str = "") -> int:
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO feedback (user_id, recommendation_id, rating, comment) VALUES (?, ?, ?, ?)",
            (user_id, recommendation_id, rating, comment),
        )
        return cur.lastrowid


def get_recent_recommendations(user_id: int, context: Optional[str] = None, limit: int = 20):
    with get_cursor() as cur:
        if context:
            cur.execute(
                "SELECT * FROM recommendations WHERE user_id = ? AND context = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, context, limit),
            )
        else:
            cur.execute(
                "SELECT * FROM recommendations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            )
        return cur.fetchall()
