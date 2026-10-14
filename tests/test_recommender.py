"""Tests for src/recommendation/recommender.py and ranking.py."""

from src.database import repositories as repo
from src.recommendation.recommender import recommend_next_foods
from src.recommendation.ranking import cosine_similarity, score_food_for_remaining_targets


def test_recommend_next_foods_respects_allergy(seeded_db, sample_user_id):
    repo.set_user_preferences(sample_user_id, "allergy", ["peanut"])
    results = recommend_next_foods(sample_user_id, remaining_calories=500, remaining_protein_g=30,
                                    diet_type="vegetarian", top_n=20)
    for r in results:
        assert "peanut" not in [a.lower() for a in r.food.allergen_list()]


def test_recommend_next_foods_respects_dietary_type(seeded_db, sample_user_id):
    results = recommend_next_foods(sample_user_id, remaining_calories=500, remaining_protein_g=30,
                                    diet_type="vegan", top_n=50)
    for r in results:
        assert r.food.dietary_type == "vegan"


def test_recommend_next_foods_empty_database_returns_empty(temp_db):
    # No foods seeded at all -- must not crash, should return an empty list.
    from src.database.models import UserProfile
    user_id = repo.create_user(UserProfile(id=None, name="Empty DB User", age=25, sex="male",
                                            height_cm=175.0, weight_kg=70.0))
    results = recommend_next_foods(user_id, remaining_calories=500, remaining_protein_g=30, diet_type="vegan")
    assert results == []


def test_scores_are_sorted_descending(seeded_db, sample_user_id):
    results = recommend_next_foods(sample_user_id, remaining_calories=800, remaining_protein_g=50,
                                    diet_type="vegetarian", top_n=10)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_cosine_similarity_identical_vectors_is_one():
    v = [1.0, 2.0, 3.0]
    assert cosine_similarity(v, v) == 1.0


def test_cosine_similarity_zero_vector_is_zero():
    assert cosine_similarity([0, 0, 0], [1, 2, 3]) == 0.0


def test_score_food_favorite_bonus_increases_score(seeded_db):
    foods = repo.search_foods(query_text="banana")
    assert foods, "Expected 'banana' to exist in the demo dataset"
    banana = foods[0]

    without_favorite = score_food_for_remaining_targets(banana, 500, 20, favorite_foods=[], preferred_cuisine="")
    with_favorite = score_food_for_remaining_targets(banana, 500, 20, favorite_foods=["banana"], preferred_cuisine="")
    assert with_favorite.score > without_favorite.score
