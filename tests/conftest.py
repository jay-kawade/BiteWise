"""
conftest.py
-------------------------------------------------------------------------------
Shared pytest fixtures. The most important one is `temp_db`, which points
the whole application at a brand-new, empty SQLite file for the duration of
one test, so tests never touch (or are affected by) the real
data/processed/nutrition_app.db used when actually running the app.
-------------------------------------------------------------------------------
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from src.utils import config


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    """Point the app at a fresh, empty SQLite database file for this test only."""
    db_path = tmp_path / "test_nutrition_app.db"
    monkeypatch.setattr(config, "DATABASE_PATH", db_path)

    from src.database.db import initialize_database
    initialize_database()

    return db_path


@pytest.fixture()
def seeded_db(temp_db):
    """A temp_db that additionally has the demo food dataset loaded."""
    from src.database.seed import seed_foods_from_csv
    seed_foods_from_csv()
    return temp_db


@pytest.fixture()
def sample_user_id(seeded_db):
    """Creates one basic user profile in the seeded temp database and returns its id."""
    from src.database import repositories as repo
    from src.database.models import UserProfile

    profile = UserProfile(
        id=None, name="Test User", age=22, sex="female", height_cm=160.0, weight_kg=58.0,
        activity_level="moderately_active", goal="maintenance", diet_type="vegetarian",
        cuisine_preference="indian",
    )
    return repo.create_user(profile)
