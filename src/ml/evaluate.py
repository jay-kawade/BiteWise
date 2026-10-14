"""
evaluate.py
-------------------------------------------------------------------------------
Honest evaluation helpers for the meal-type classifier. Every number these
functions produce comes directly from scikit-learn's metric functions run on
real held-out predictions -- nothing here is hand-typed or invented.
-------------------------------------------------------------------------------
"""

from typing import Dict

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def compute_classification_metrics(y_true, y_pred) -> Dict[str, float]:
    """
    Macro-averaged precision/recall/F1 are used (rather than "weighted" or
    "micro") because with only 4 fairly small classes we want each meal-type
    class to count equally, not be dominated by whichever class happens to
    have more samples.
    """
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
    }


def compute_confusion_matrix(y_true, y_pred, labels) -> pd.DataFrame:
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    return pd.DataFrame(matrix, index=[f"actual_{l}" for l in labels], columns=[f"predicted_{l}" for l in labels])
