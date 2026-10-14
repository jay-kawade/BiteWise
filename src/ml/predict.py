"""
predict.py
-------------------------------------------------------------------------------
Inference-time code: load the already-trained model ONCE (Section 35:
"load trained models once") and use it to predict a probable meal_type for a
food's nutrition profile, with class probabilities so the caller can show
confidence and (in the UI) decline to act on a low-confidence guess.
-------------------------------------------------------------------------------
"""

from dataclasses import dataclass
from typing import Dict, Optional

from src.ml.model_utils import load_model
from src.ml.preprocessing import features_from_nutrition_dict
from src.utils.logger import get_logger

logger = get_logger(__name__)

_CACHED_PIPELINE = None
_CACHED_METADATA = None


@dataclass
class MealTypePrediction:
    predicted_meal_type: str
    confidence: float
    class_probabilities: Dict[str, float]
    model_name: str


def _get_cached_model():
    global _CACHED_PIPELINE, _CACHED_METADATA
    if _CACHED_PIPELINE is None:
        _CACHED_PIPELINE, _CACHED_METADATA = load_model()
    return _CACHED_PIPELINE, _CACHED_METADATA


def is_model_available() -> bool:
    pipeline, _ = _get_cached_model()
    return pipeline is not None


def predict_meal_type(nutrition: dict, serving_size_g: float, dietary_type: str = "vegetarian") -> Optional[MealTypePrediction]:
    """
    nutrition dict keys expected: calories, protein_g, carbohydrates_g,
    fat_g, fiber_g, sugar_g, sodium_mg, saturated_fat_g.

    Returns None if no trained model is available yet (the UI/agent must
    handle this gracefully -- e.g. by telling the user to run the training
    script, or by simply not showing the ML-based suggestion).
    """
    pipeline, metadata = _get_cached_model()
    if pipeline is None:
        logger.warning("No trained meal-type model found. Run `python -m src.ml.train` first.")
        return None

    X = features_from_nutrition_dict(nutrition, serving_size_g, dietary_type)
    predicted_label = pipeline.predict(X)[0]

    probabilities = {}
    if hasattr(pipeline, "predict_proba"):
        proba = pipeline.predict_proba(X)[0]
        classes = pipeline.classes_
        probabilities = {cls: round(float(p), 4) for cls, p in zip(classes, proba)}

    confidence = probabilities.get(predicted_label, 0.0)
    model_name = metadata.get("selected_model", "unknown") if metadata else "unknown"

    return MealTypePrediction(
        predicted_meal_type=predicted_label,
        confidence=confidence,
        class_probabilities=probabilities,
        model_name=model_name,
    )


def get_model_metadata() -> Optional[dict]:
    _, metadata = _get_cached_model()
    return metadata
