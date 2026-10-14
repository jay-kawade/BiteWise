"""
preprocessing.py
-------------------------------------------------------------------------------
Prepares the food database for the machine learning task used in this
project.

--------------------------------------------------------------------------
THE ML TASK, EXPLAINED (for the viva)
--------------------------------------------------------------------------
Problem type chosen : MULTI-CLASS CLASSIFICATION
Question the model answers:
    "Given a food's nutrition profile (calories, protein, carbs, fat, fiber,
    sugar, sodium, saturated fat -- all normalized per 100g -- and its
    dietary type), which meal (breakfast / lunch / dinner / snack) does it
    most likely belong to?"

Why this task, and not a fabricated "predict disease risk" model:
    1. It uses a REAL column already present in our food database
       (meal_type), so we are not inventing labels.
    2. It is genuinely useful: when a user or an admin adds a NEW food to
       the database without specifying a meal type, the trained model can
       suggest one, and the AI assistant / recommendation engine can use
       the model's probability scores (not just a hard label) to decide
       which meal slot a food fits best.
    3. It is honestly evaluable with standard classification metrics
       (accuracy, precision, recall, F1, confusion matrix) on a held-out
       test split -- see src/ml/evaluate.py and docs/ml_methodology.md.

This is DELIBERATELY separate from:
    - the deterministic nutrition calculator (src/nutrition/) -- plain
      arithmetic formulas, not learned from data.
    - the recommendation engine (src/recommendation/) -- transparent
      weighted-scoring / nutrient-distance ranking, not a trained model.
The UI must always label which of the three produced a given number.
--------------------------------------------------------------------------
"""

from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

from src.database import repositories as repo

# Features are computed PER 100 GRAMS so that a small snack and a large meal
# are compared fairly regardless of their serving_size_g.
NUMERIC_FEATURES = [
    "calories_per_100g", "protein_per_100g", "carbs_per_100g", "fat_per_100g",
    "fiber_per_100g", "sugar_per_100g", "sodium_per_100g", "sat_fat_per_100g",
]
CATEGORICAL_FEATURES = ["dietary_type"]
TARGET_COLUMN = "meal_type"


@dataclass
class MLDataset:
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    full_df: pd.DataFrame


def load_foods_as_dataframe() -> pd.DataFrame:
    """Read every food from the database (already seeded from the CSV)."""
    foods = repo.list_all_foods()
    records = [
        {
            "name": f.name,
            "serving_size_g": f.serving_size_g,
            "calories": f.calories,
            "protein_g": f.protein_g,
            "carbohydrates_g": f.carbohydrates_g,
            "fat_g": f.fat_g,
            "fiber_g": f.fiber_g,
            "sugar_g": f.sugar_g,
            "sodium_mg": f.sodium_mg,
            "saturated_fat_g": f.saturated_fat_g,
            "dietary_type": f.dietary_type,
            "meal_type": f.meal_type,
        }
        for f in foods
    ]
    return pd.DataFrame(records)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw per-serving nutrition columns into per-100g features.
    Rows with a missing/zero serving size are dropped (cannot be normalized)
    -- this IS the "missing value handling" step of the pipeline (Section 24).
    """
    df = df.copy()
    df = df.dropna(subset=["serving_size_g"])
    df = df[df["serving_size_g"] > 0]

    scale = 100.0 / df["serving_size_g"]
    df["calories_per_100g"] = df["calories"] * scale
    df["protein_per_100g"] = df["protein_g"] * scale
    df["carbs_per_100g"] = df["carbohydrates_g"] * scale
    df["fat_per_100g"] = df["fat_g"] * scale
    df["fiber_per_100g"] = df["fiber_g"] * scale
    df["sugar_per_100g"] = df["sugar_g"] * scale
    df["sodium_per_100g"] = df["sodium_mg"] * scale
    df["sat_fat_per_100g"] = df["saturated_fat_g"] * scale
    return df


def build_ml_dataset(test_size: float = 0.25, random_state: int = 42) -> MLDataset:
    """
    Load, engineer features, and produce a stratified train/test split.

    `stratify=y` keeps the proportion of each meal_type class the same in
    both the train and test sets, which matters a lot for a dataset this
    small (see docs/ml_methodology.md for the honest discussion of dataset
    size limitations).
    """
    raw_df = load_foods_as_dataframe()
    df = engineer_features(raw_df)

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    return MLDataset(X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test, full_df=df)


def features_from_nutrition_dict(nutrition: dict, serving_size_g: float, dietary_type: str = "vegetarian") -> pd.DataFrame:
    """
    Build a single-row feature DataFrame from a raw nutrition dict (e.g. one
    coming from the OCR scanner or a manually entered food), so it can be
    fed into the trained model for a prediction. Keys expected in
    `nutrition`: calories, protein_g, carbohydrates_g, fat_g, fiber_g,
    sugar_g, sodium_mg, saturated_fat_g.
    """
    serving_size_g = serving_size_g if serving_size_g and serving_size_g > 0 else 100.0
    scale = 100.0 / serving_size_g
    row = {
        "calories_per_100g": nutrition.get("calories", 0.0) * scale,
        "protein_per_100g": nutrition.get("protein_g", 0.0) * scale,
        "carbs_per_100g": nutrition.get("carbohydrates_g", 0.0) * scale,
        "fat_per_100g": nutrition.get("fat_g", 0.0) * scale,
        "fiber_per_100g": nutrition.get("fiber_g", 0.0) * scale,
        "sugar_per_100g": nutrition.get("sugar_g", 0.0) * scale,
        "sodium_per_100g": nutrition.get("sodium_mg", 0.0) * scale,
        "sat_fat_per_100g": nutrition.get("saturated_fat_g", 0.0) * scale,
        "dietary_type": dietary_type,
    }
    return pd.DataFrame([row])
