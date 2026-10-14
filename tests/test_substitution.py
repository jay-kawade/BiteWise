"""Tests for src/recommendation/substitution.py."""

from src.recommendation.substitution import find_food_by_name, find_substitutes


def test_find_food_by_name_exact_match(seeded_db):
    food = find_food_by_name("Paneer (cottage cheese)")
    assert food is not None
    assert food.name == "Paneer (cottage cheese)"


def test_find_food_by_name_no_match_returns_none(seeded_db):
    assert find_food_by_name("Nonexistent Food XYZ") is None


def test_substitutes_exclude_the_original_food(seeded_db, sample_user_id):
    original = find_food_by_name("Paneer (cottage cheese)")
    results = find_substitutes(original, sample_user_id, top_n=10)
    names = [r.food.name for r in results]
    assert original.name not in names


def test_substitutes_respect_dietary_type(seeded_db, sample_user_id):
    # sample_user_id fixture uses diet_type='vegetarian'
    original = find_food_by_name("Paneer (cottage cheese)")
    results = find_substitutes(original, sample_user_id, top_n=20)
    for r in results:
        assert r.food.dietary_type in {"vegan", "vegetarian"}


def test_substitutes_are_ranked_by_score_descending(seeded_db, sample_user_id):
    original = find_food_by_name("Paneer (cottage cheese)")
    results = find_substitutes(original, sample_user_id, top_n=10)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_tofu_ranks_above_a_carb_staple_for_paneer_substitution(seeded_db, sample_user_id):
    """
    Regression test: nutrient-similarity scoring must be sensitive to macro
    COMPOSITION (protein/fat-heavy vs carb-heavy), not just raw calorie
    magnitude. See src/recommendation/ranking.py's _REFERENCE_SCALE comment.
    """
    original = find_food_by_name("Paneer (cottage cheese)")
    results = find_substitutes(original, sample_user_id, top_n=20)
    names_in_order = [r.food.name for r in results]
    assert "Tofu (firm)" in names_in_order
    if "Roti (whole wheat)" in names_in_order:
        assert names_in_order.index("Tofu (firm)") < names_in_order.index("Roti (whole wheat)")
