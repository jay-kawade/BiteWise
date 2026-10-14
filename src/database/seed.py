"""
seed.py
-------------------------------------------------------------------------------
Loads the food database from data/sample/foods_sample.csv into the SQLite
`foods` table. Runs once automatically when the app starts (see
app/main.py) if the table is currently empty -- it will never duplicate
rows on subsequent runs.

To use a different/real dataset instead of the bundled demo one, point
SAMPLE_FOODS_CSV (in src/utils/config.py) at your cleaned CSV file. It must
have the same column names as data/sample/foods_sample.csv.
-------------------------------------------------------------------------------
"""

import pandas as pd

from src.database import repositories as repo
from src.database.db import initialize_database, is_database_seeded
from src.database.models import Food
from src.utils import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def seed_foods_from_csv(csv_path=None) -> int:
    csv_path = csv_path or config.SAMPLE_FOODS_CSV
    df = pd.read_csv(csv_path)

    inserted = 0
    for _, row in df.iterrows():
        food = Food(
            id=None,
            name=str(row["name"]),
            category=str(row["category"]),
            serving_size_g=float(row["serving_size_g"]),
            calories=float(row["calories"]),
            protein_g=float(row["protein_g"]),
            carbohydrates_g=float(row["carbohydrates_g"]),
            fat_g=float(row["fat_g"]),
            fiber_g=float(row["fiber_g"]),
            sugar_g=float(row["sugar_g"]),
            sodium_mg=float(row["sodium_mg"]),
            saturated_fat_g=float(row["saturated_fat_g"]),
            dietary_type=str(row["dietary_type"]),
            meal_type=str(row["meal_type"]),
            cuisine=str(row.get("cuisine", "other")),
            allergens=str(row.get("allergens", "")) if pd.notna(row.get("allergens", "")) else "",
            tags=str(row.get("tags", "")) if pd.notna(row.get("tags", "")) else "",
            source=str(row.get("source", "demo_reference")),
        )
        repo.insert_food(food)
        inserted += 1

    logger.info("Seeded %d foods from %s", inserted, csv_path)
    return inserted


def ensure_seeded() -> None:
    """Initialize the schema and seed demo foods, but only if needed."""
    initialize_database()
    if not is_database_seeded():
        seed_foods_from_csv()
    else:
        logger.info("Foods table already seeded (%d rows) -- skipping.", repo.count_foods())


if __name__ == "__main__":
    ensure_seeded()
