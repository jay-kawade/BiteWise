"""Tests for src/database/repositories.py -- database operations."""

from src.database import repositories as repo
from src.database.models import FoodLogEntry, UserProfile


def test_create_and_get_user(temp_db):
    profile = UserProfile(id=None, name="Alice", age=30, sex="female", height_cm=165.0,
                           weight_kg=60.0, diet_type="vegan")
    user_id = repo.create_user(profile)
    fetched = repo.get_user(user_id)
    assert fetched is not None
    assert fetched.name == "Alice"
    assert fetched.diet_type == "vegan"


def test_get_nonexistent_user_returns_none(temp_db):
    assert repo.get_user(999) is None


def test_update_user(temp_db):
    profile = UserProfile(id=None, name="Bob", age=25, sex="male", height_cm=175.0, weight_kg=70.0)
    user_id = repo.create_user(profile)
    fetched = repo.get_user(user_id)
    fetched.weight_kg = 72.0
    repo.update_user(fetched)
    assert repo.get_user(user_id).weight_kg == 72.0


def test_user_preferences_roundtrip(temp_db):
    profile = UserProfile(id=None, name="Carol", age=28, sex="female", height_cm=160.0, weight_kg=55.0)
    user_id = repo.create_user(profile)
    repo.set_user_preferences(user_id, "allergy", ["peanut", "milk"])
    values = repo.get_preference_values(user_id, "allergy")
    assert set(values) == {"peanut", "milk"}

    # Replacing should clear the old list, not append to it.
    repo.set_user_preferences(user_id, "allergy", ["soy"])
    assert repo.get_preference_values(user_id, "allergy") == ["soy"]


def test_food_search_respects_dietary_hierarchy(seeded_db):
    vegan_results = repo.search_foods(dietary_type="vegan")
    for food in vegan_results:
        assert food.dietary_type == "vegan"

    non_veg_results = repo.search_foods(dietary_type="non_vegetarian")
    dietary_types_present = {f.dietary_type for f in non_veg_results}
    # A non-vegetarian user should see foods of every dietary type.
    assert "vegan" in dietary_types_present
    assert "non_vegetarian" in dietary_types_present


def test_food_search_excludes_allergens(seeded_db):
    results = repo.search_foods(exclude_allergens=["peanut"])
    for food in results:
        assert "peanut" not in [a.lower() for a in food.allergen_list()]


def test_food_search_empty_database_returns_empty_list(temp_db):
    assert repo.search_foods() == []


def test_log_and_retrieve_food(seeded_db, sample_user_id):
    entry = FoodLogEntry(
        id=None, user_id=sample_user_id, food_id=None, food_name="Test Food", meal_type="lunch",
        quantity_servings=1.0, calories=200, protein_g=10, carbohydrates_g=20, fat_g=5,
    )
    log_id = repo.log_food(entry, log_date="2024-01-01")
    logs = repo.get_food_logs_for_date(sample_user_id, "2024-01-01")
    assert len(logs) == 1
    assert logs[0].food_name == "Test Food"

    repo.delete_food_log(log_id)
    assert repo.get_food_logs_for_date(sample_user_id, "2024-01-01") == []
