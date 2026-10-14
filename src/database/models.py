"""
models.py
-------------------------------------------------------------------------------
Simple Python dataclasses that mirror the database tables in schema.sql.

We use plain dataclasses instead of a full ORM (like SQLAlchemy) on purpose:
this project's team is composed of Biotechnology students, and a lightweight
"data holder" class is much easier to read and debug than ORM "magic". The
actual reading/writing to SQLite happens in repositories.py, which returns
these dataclasses.
-------------------------------------------------------------------------------
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UserProfile:
    id: Optional[int]
    name: str
    age: int
    sex: str                       # 'male' | 'female' | 'other'
    height_cm: float
    weight_kg: float
    activity_level: str = "moderately_active"
    exercise_frequency_per_week: int = 0
    exercise_type: str = ""
    sleep_hours: float = 7.0
    goal: str = "maintenance"      # weight_loss | maintenance | weight_gain | muscle_gain
    diet_type: str = "vegetarian"  # vegan | vegetarian | eggetarian | non_vegetarian
    cuisine_preference: str = "indian"
    budget_preference: str = "medium"
    cooking_time_preference: str = "medium"
    meals_per_day: int = 4
    health_notes: str = ""


@dataclass
class UserPreference:
    id: Optional[int]
    user_id: int
    preference_type: str  # favorite_food | disliked_food | allergy | avoid_ingredient
    value: str


@dataclass
class NutritionTargets:
    id: Optional[int]
    user_id: int
    bmi: float
    bmi_category: str
    bmr_kcal: float
    tdee_kcal: float
    calorie_target_kcal: float
    protein_target_g: float
    carb_target_g: float
    fat_target_g: float
    fiber_target_g: float
    calculated_at: Optional[str] = None


@dataclass
class Food:
    id: Optional[int]
    name: str
    category: str
    serving_size_g: float
    calories: float
    protein_g: float
    carbohydrates_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float
    sodium_mg: float
    saturated_fat_g: float
    dietary_type: str
    meal_type: str
    cuisine: str = "other"
    allergens: str = ""     # "|"-separated
    tags: str = ""          # "|"-separated
    source: str = "demo_reference"

    def allergen_list(self) -> List[str]:
        return [a.strip() for a in self.allergens.split("|") if a.strip()]

    def tag_list(self) -> List[str]:
        return [t.strip() for t in self.tags.split("|") if t.strip()]


@dataclass
class FoodLogEntry:
    id: Optional[int]
    user_id: int
    food_id: Optional[int]
    food_name: str
    meal_type: str
    quantity_servings: float
    calories: float
    protein_g: float
    carbohydrates_g: float
    fat_g: float
    fiber_g: float = 0.0
    sugar_g: float = 0.0
    sodium_mg: float = 0.0
    log_source: str = "manual"
    logged_at: Optional[str] = None
    log_date: Optional[str] = None


@dataclass
class ScannedFood:
    id: Optional[int]
    user_id: int
    raw_ocr_text: str
    parsed_nutrition: dict
    parsed_ingredients: List[str]
    allergen_warnings: List[str]
    confidence_score: float
    ocr_mode: str
    created_at: Optional[str] = None


@dataclass
class MealPlan:
    id: Optional[int]
    user_id: int
    plan_date: str
    plan_type: str
    target_calories: float
    target_protein_g: float
    total_calories: float = 0.0
    total_protein_g: float = 0.0
    items: List["MealPlanItem"] = field(default_factory=list)


@dataclass
class MealPlanItem:
    id: Optional[int]
    meal_plan_id: int
    meal_slot: str
    food_id: Optional[int]
    food_name: str
    quantity_servings: float = 1.0
