"""
eda_script.py
-------------------------------------------------------------------------------
Exploratory Data Analysis for the food dataset used to train the meal-type
classifier (see docs/ml_methodology.md). Run this before/alongside
`python -m src.ml.train` to understand the data the model is learning from.

Run with:
    python notebooks/eda_script.py
-------------------------------------------------------------------------------
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.seed import ensure_seeded
from src.ml.preprocessing import NUMERIC_FEATURES, engineer_features, load_foods_as_dataframe


def main():
    ensure_seeded()
    raw_df = load_foods_as_dataframe()
    df = engineer_features(raw_df)

    print(f"Total foods in database: {len(df)}\n")

    print("Class balance (meal_type) -- the ML classification target:")
    print(df["meal_type"].value_counts())
    print()

    print("Class balance (dietary_type):")
    print(df["dietary_type"].value_counts())
    print()

    print("Summary statistics of engineered per-100g features:")
    print(df[NUMERIC_FEATURES].describe().round(2))
    print()

    print("Correlation between per-100g features:")
    print(df[NUMERIC_FEATURES].corr().round(2))


if __name__ == "__main__":
    main()
