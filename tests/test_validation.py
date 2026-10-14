"""Tests for src/nutrition/validation.py -- input sanity checks."""

from src.nutrition.validation import validate_food_log_quantity, validate_profile_inputs


def _valid_kwargs(**overrides):
    base = dict(
        name="Test", age=25, sex="female", height_cm=165.0, weight_kg=60.0,
        activity_level="moderately_active", goal="maintenance", diet_type="vegetarian",
        sleep_hours=7.0,
    )
    base.update(overrides)
    return base


def test_valid_profile_has_no_errors():
    assert validate_profile_inputs(**_valid_kwargs()) == []


def test_empty_name_is_rejected():
    errors = validate_profile_inputs(**_valid_kwargs(name="   "))
    assert any("name" in e.lower() for e in errors)


def test_age_out_of_range_is_rejected():
    errors = validate_profile_inputs(**_valid_kwargs(age=5))
    assert any("age" in e.lower() for e in errors)


def test_invalid_height_is_rejected():
    errors = validate_profile_inputs(**_valid_kwargs(height_cm=-10))
    assert any("height" in e.lower() for e in errors)


def test_invalid_weight_is_rejected():
    errors = validate_profile_inputs(**_valid_kwargs(weight_kg=1000))
    assert any("weight" in e.lower() for e in errors)


def test_invalid_sex_is_rejected():
    errors = validate_profile_inputs(**_valid_kwargs(sex="unknown"))
    assert any("sex" in e.lower() for e in errors)


def test_invalid_activity_level_is_rejected():
    errors = validate_profile_inputs(**_valid_kwargs(activity_level="super_active"))
    assert any("activity" in e.lower() for e in errors)


def test_invalid_goal_is_rejected():
    errors = validate_profile_inputs(**_valid_kwargs(goal="get_shredded"))
    assert any("goal" in e.lower() for e in errors)


def test_invalid_diet_type_is_rejected():
    errors = validate_profile_inputs(**_valid_kwargs(diet_type="carnivore"))
    assert any("diet" in e.lower() for e in errors)


def test_multiple_errors_are_all_reported():
    errors = validate_profile_inputs(**_valid_kwargs(age=200, height_cm=-1, weight_kg=-1))
    assert len(errors) >= 3


def test_food_log_quantity_must_be_positive():
    assert validate_food_log_quantity(0) != []
    assert validate_food_log_quantity(-1) != []
    assert validate_food_log_quantity(1.0) == []


def test_food_log_quantity_flags_unusually_large_values():
    assert validate_food_log_quantity(50) != []
