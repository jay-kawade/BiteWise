"""
train.py
-------------------------------------------------------------------------------
Reproducible training script for the meal-type classifier.

Run it directly from the project root:
    python -m src.ml.train

What it does (Section 24's ML pipeline, applied to this project's task):
    1. Load the food dataset from the database.
    2. Engineer per-100g nutrition features (see preprocessing.py).
    3. Split into train/test (stratified, so class balance is preserved).
    4. Train THREE candidate models behind the identical preprocessing
       pipeline, so the comparison is fair:
           - Logistic Regression   (simple, interpretable linear baseline)
           - Decision Tree         (captures non-linear thresholds, interpretable)
           - Random Forest         (usually more accurate, ensemble of trees)
    5. Evaluate all three on the held-out test set with the same metrics.
    6. Pick the model with the best macro-F1 score (a single, honest,
       pre-declared selection rule -- not picked after the fact to look good).
    7. Save the winning pipeline (preprocessing + model together) and a
       metadata JSON file with every candidate's metrics, so nothing is
       hidden even if a simpler model wins.

HONESTY NOTE: the bundled demo dataset has only ~100 food rows. With so few
examples, test-set metrics will have wide statistical uncertainty. This is
disclosed in docs/ml_methodology.md and shown in the app's "Evaluation"
section rather than hidden or dressed up.
-------------------------------------------------------------------------------
"""

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from src.ml.evaluate import compute_classification_metrics, compute_confusion_matrix
from src.ml.model_utils import build_preprocessor, save_model
from src.ml.preprocessing import build_ml_dataset
from src.utils.logger import get_logger

logger = get_logger(__name__)

RANDOM_STATE = 42

CANDIDATE_MODELS = {
    "logistic_regression": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
    "decision_tree": DecisionTreeClassifier(max_depth=5, random_state=RANDOM_STATE),
    "random_forest": RandomForestClassifier(n_estimators=200, max_depth=6, random_state=RANDOM_STATE),
}


def train_and_select_best_model():
    dataset = build_ml_dataset(test_size=0.25, random_state=RANDOM_STATE)
    labels = sorted(dataset.y_train.unique())

    logger.info("Training dataset: %d rows train, %d rows test, classes=%s",
                len(dataset.X_train), len(dataset.X_test), labels)

    results = {}
    fitted_pipelines = {}

    for model_name, estimator in CANDIDATE_MODELS.items():
        pipeline = Pipeline(steps=[
            ("preprocessor", build_preprocessor()),
            ("classifier", estimator),
        ])
        pipeline.fit(dataset.X_train, dataset.y_train)
        y_pred = pipeline.predict(dataset.X_test)

        metrics = compute_classification_metrics(dataset.y_test, y_pred)
        confusion = compute_confusion_matrix(dataset.y_test, y_pred, labels)

        results[model_name] = {"metrics": metrics, "confusion_matrix": confusion.to_dict()}
        fitted_pipelines[model_name] = pipeline

        logger.info("%s -> %s", model_name, metrics)

    # Selection rule declared BEFORE looking at results: highest macro-F1 wins.
    best_model_name = max(results, key=lambda name: results[name]["metrics"]["f1_macro"])
    best_pipeline = fitted_pipelines[best_model_name]

    feature_importance = _extract_feature_importance(best_pipeline)

    metadata = {
        "task": "multi-class classification of food meal_type from nutrition profile",
        "target_column": "meal_type",
        "classes": labels,
        "dataset_size_total": len(dataset.full_df),
        "dataset_size_train": len(dataset.X_train),
        "dataset_size_test": len(dataset.X_test),
        "dataset_note": (
            "Trained on the bundled demo food dataset (~100 rows, see "
            "data/sample/README.md). Metrics below have wide statistical "
            "uncertainty at this sample size and should be read as a "
            "methodology demonstration, not a production accuracy claim."
        ),
        "candidates_compared": list(CANDIDATE_MODELS.keys()),
        "results_by_model": results,
        "selected_model": best_model_name,
        "selection_rule": "highest macro-averaged F1 score on the held-out test split",
        "feature_importance": feature_importance,
    }

    save_model(best_pipeline, metadata)
    logger.info("Selected model: %s (f1_macro=%.3f). Saved to models/.",
                best_model_name, results[best_model_name]["metrics"]["f1_macro"])

    return best_model_name, metadata


def _extract_feature_importance(pipeline: Pipeline):
    """
    For tree-based models we can report scikit-learn's built-in
    feature_importances_ (Section 25: explainability). For Logistic
    Regression we report the absolute coefficient magnitudes instead.
    These are GLOBAL importances describing the whole model's behaviour --
    not a causal or medical explanation for any single prediction.
    """
    classifier = pipeline.named_steps["classifier"]
    preprocessor = pipeline.named_steps["preprocessor"]
    try:
        feature_names = list(preprocessor.get_feature_names_out())
    except Exception:
        feature_names = None

    if hasattr(classifier, "feature_importances_"):
        importances = classifier.feature_importances_.tolist()
    elif hasattr(classifier, "coef_"):
        importances = abs(classifier.coef_).mean(axis=0).tolist()
    else:
        return {}

    if feature_names and len(feature_names) == len(importances):
        pairs = sorted(zip(feature_names, importances), key=lambda p: p[1], reverse=True)
        return {name: round(float(value), 4) for name, value in pairs}
    return {"raw_importances": [round(float(v), 4) for v in importances]}


if __name__ == "__main__":
    train_and_select_best_model()
