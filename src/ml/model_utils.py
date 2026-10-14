"""
model_utils.py
-------------------------------------------------------------------------------
Shared helpers for building the scikit-learn preprocessing pipeline and for
saving/loading the trained model together with its preprocessing (so
inference never accidentally uses mismatched preprocessing -- Section 24:
"save preprocessing and model together where practical").
-------------------------------------------------------------------------------
"""

import json
from datetime import datetime, timezone

import joblib
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.ml.preprocessing import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from src.utils import config


def build_preprocessor() -> ColumnTransformer:
    """
    ColumnTransformer = apply different preprocessing to different columns:
      - numeric nutrition columns: fill any missing values with the median,
        then scale to mean 0 / std 1 (important for Logistic Regression).
      - categorical dietary_type: fill missing with the most frequent value,
        then one-hot encode (turn "vegan"/"vegetarian"/etc. into 0/1 columns).
    Using a Pipeline + ColumnTransformer (instead of doing this by hand)
    prevents data leakage: the scaler's mean/std are learned ONLY from the
    training split, never the test split.
    """
    numeric_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer(transformers=[
        ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
    ])


def save_model(pipeline, metadata: dict) -> None:
    config.ensure_directories()
    joblib.dump(pipeline, config.MEAL_TYPE_MODEL_PATH)
    metadata = dict(metadata)
    metadata["saved_at"] = datetime.now(timezone.utc).isoformat()
    with open(config.MODEL_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def load_model():
    """Returns (pipeline, metadata) or (None, None) if no model has been trained yet."""
    if not config.MEAL_TYPE_MODEL_PATH.exists():
        return None, None
    pipeline = joblib.load(config.MEAL_TYPE_MODEL_PATH)
    metadata = {}
    if config.MODEL_METADATA_PATH.exists():
        with open(config.MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    return pipeline, metadata
