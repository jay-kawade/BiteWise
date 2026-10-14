"""Tests for src/agent/tools.py -- the functions the AI assistant can call."""

import pytest

from src.agent import tools
from src.agent.orchestrator import handle_user_message


def test_get_user_profile_unknown_user_returns_error(temp_db):
    result = tools.get_user_profile(9999)
    assert "error" in result


def test_get_user_profile_returns_preferences(seeded_db, sample_user_id):
    from src.database import repositories as repo
    repo.set_user_preferences(sample_user_id, "allergy", ["peanut"])
    profile = tools.get_user_profile(sample_user_id)
    assert profile["allergies"] == ["peanut"]


def test_log_food_with_food_id(seeded_db, sample_user_id):
    from src.database import repositories as repo
    foods = repo.search_foods(query_text="banana")
    banana = foods[0]
    result = tools.log_food(sample_user_id, banana.name, "snack", quantity_servings=2.0, food_id=banana.id)
    assert "log_id" in result
    assert result["logged"]["calories"] == round(banana.calories * 2.0, 1)


def test_log_food_without_food_id_or_nutrition_returns_error(seeded_db, sample_user_id):
    result = tools.log_food(sample_user_id, "Mystery food", "snack")
    assert "error" in result


def test_get_daily_consumption_sums_logged_foods(seeded_db, sample_user_id):
    from src.database import repositories as repo
    foods = repo.search_foods(query_text="banana")
    banana = foods[0]
    tools.log_food(sample_user_id, banana.name, "snack", quantity_servings=1.0, food_id=banana.id)
    consumption = tools.get_daily_consumption(sample_user_id)
    assert consumption["entries_count"] == 1
    assert consumption["totals"]["calories"] == pytest.approx(banana.calories, abs=0.5)


def test_suggest_substitutions_unknown_food_returns_error(seeded_db, sample_user_id):
    result = tools.suggest_substitutions(sample_user_id, "Nonexistent Food XYZ")
    assert "error" in result


def test_get_weekly_summary_no_logs_returns_message(seeded_db, sample_user_id):
    result = tools.get_weekly_summary(sample_user_id)
    assert result["days_logged"] == 0


def test_agent_refuses_medical_advice_questions(seeded_db, sample_user_id):
    response = handle_user_message(sample_user_id, "Should I change my diabetes medication?")
    assert response.mode == "safety_refusal"
    assert "healthcare professional" in response.text.lower() or "doctor" in response.text.lower()


def test_agent_handles_unknown_message_gracefully(seeded_db, sample_user_id):
    response = handle_user_message(sample_user_id, "asdkjaslkdjalksjd")
    assert response.text  # should not crash, should return some helpful text
