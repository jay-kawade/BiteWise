"""
Tests for the ML pipeline (src/ml/). These exercise the REAL training
pipeline end-to-end against the seeded demo dataset, so a broken
preprocessing step or a scikit-learn API change would be caught here.
"""

import pytest

from src.ml.evaluate import compute_classification_metrics
from src.ml.preprocessing import build_ml_dataset, engineer_features, load_foods_as_dataframe


def test_engineer_features_normalizes_per_100g(seeded_db):
    df = load_foods_as_dataframe()
    engineered = engineer_features(df)
    # Pick a row with a known serving size and check the per-100g math.
    row = engineered[engineered["name"] == "Boiled egg"].iloc[0]
    expected_calories_per_100g = row["calories"] * (100.0 / row["serving_size_g"])
    assert row["calories_per_100g"] == pytest.approx(expected_calories_per_100g)


def test_build_ml_dataset_produces_stratified_split(seeded_db):
    dataset = build_ml_dataset(test_size=0.25, random_state=42)
    assert len(dataset.X_train) > 0
    assert len(dataset.X_test) > 0
    # All 4 meal_type classes should appear in the training set.
    assert set(dataset.y_train.unique()) == {"breakfast", "lunch", "dinner", "snack"}


def test_compute_classification_metrics_perfect_predictions():
    y_true = ["a", "b", "a", "b"]
    y_pred = ["a", "b", "a", "b"]
    metrics = compute_classification_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 1.0
    assert metrics["f1_macro"] == 1.0


def test_compute_classification_metrics_all_wrong():
    y_true = ["a", "a", "a"]
    y_pred = ["b", "b", "b"]
    metrics = compute_classification_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 0.0


def test_full_training_pipeline_runs_and_selects_a_model(seeded_db, monkeypatch, tmp_path):
    from src.utils import config
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(config, "MEAL_TYPE_MODEL_PATH", tmp_path / "model.joblib")
    monkeypatch.setattr(config, "MODEL_METADATA_PATH", tmp_path / "metadata.json")

    from src.ml.train import train_and_select_best_model
    best_model_name, metadata = train_and_select_best_model()

    assert best_model_name in {"logistic_regression", "decision_tree", "random_forest"}
    assert 0.0 <= metadata["results_by_model"][best_model_name]["metrics"]["f1_macro"] <= 1.0
    assert (tmp_path / "model.joblib").exists()
    assert (tmp_path / "metadata.json").exists()
