# ML Methodology

## 1. Problem framing

Before picking a model, the dataset (105 foods, each with 8 nutrition
fields plus categorical dietary type and a meal_type label) was inspected
to decide which ML formulation fits it:

- **Not regression** — there is no single continuous target that matters
  more than a categorical one for this dataset; the deterministic nutrition
  calculator already handles all continuous "predictions" (BMR, calorie
  targets, etc.) with cited formulas, so those must NOT be re-solved by an
  opaque model (this would violate the requirement to clearly separate
  calculated values from ML predictions).
- **Not pure recommendation/ranking** — the recommendation engine already
  has a well-defined, explainable formulation (weighted nutrient-distance
  scoring) that does not need/benefit from a trained model given the
  dataset size.
- **Classification fits well** — the food database already contains a
  categorical label (`meal_type`) that is genuinely useful to predict for
  a NEW or SCANNED food (which has no `meal_type` supplied), so this was
  chosen as the ML task.

**Task**: multi-class classification. **Input features**: 8
nutrition values normalized to per-100g (to remove serving-size bias) plus
one-hot encoded dietary type. **Target**: `meal_type` ∈
{breakfast, lunch, dinner, snack}.

## 2. Why per-100g normalization

A 40g roti and a 300g biryani portion have very different absolute
calorie/protein numbers even if their underlying "density" is similar.
Normalizing to a common 100g basis lets the model compare foods on their
nutrient *profile* rather than their portion size.

## 3. Candidate models and why they were chosen

| Model | Why it was included |
|---|---|
| Logistic Regression | Simple, fast, interpretable linear baseline. Establishes whether the classes are linearly separable in the engineered feature space. |
| Decision Tree (max_depth=5) | Captures non-linear thresholds (e.g. "if sugar > 15g/100g AND protein < 5g/100g, likely a snack"), and is directly interpretable by printing its rules. |
| Random Forest (200 trees, max_depth=6) | An ensemble that usually improves on a single tree's accuracy/robustness, and provides feature importance for explainability (Section 25). |

All three share the *exact same* preprocessing pipeline
(`src/ml/model_utils.py::build_preprocessor`) so the comparison is fair —
only the final classifier differs.

## 4. Preventing data leakage

- `train_test_split(..., stratify=y)` is applied **before** any
  preprocessing is fit.
- The `StandardScaler` and `OneHotEncoder` live inside the same
  `sklearn.pipeline.Pipeline` as the classifier and are fit only on
  `X_train` (scikit-learn's `Pipeline.fit` guarantees this) — the test set
  never influences preprocessing parameters.
- The trained pipeline (preprocessing + model together) is what gets
  saved to `models/meal_type_classifier.joblib`, so inference always uses
  matching preprocessing.

## 5. Model selection rule

The model with the **highest macro-averaged F1 score** on the held-out
test set is selected. Macro averaging (rather than micro/weighted) was
chosen so that a smaller class (e.g. "breakfast", with fewer examples) is
not ignored in favor of optimizing for the majority class. This rule is
declared in code (`src/ml/train.py`) *before* looking at results, so the
selection is not "whichever model looks best after the fact."

## 6. Evaluation metrics reported

- Accuracy, precision (macro), recall (macro), F1 (macro) — for every
  candidate model, not just the winner.
- A full confusion matrix for the selected model.
- Global feature importance (Random Forest's `feature_importances_`, or
  Logistic Regression's coefficient magnitudes) — see Section 7.

All of these numbers are produced live by `src/ml/train.py` and can be
viewed in the app's **Settings > Model Evaluation** tab. They are NOT
hand-typed anywhere.

## 7. Explainability (Section 25)

The saved metadata JSON includes global feature importance for the
selected model. This describes which nutrition features the model relies
on **overall** (e.g. "sugar_per_100g was the most influential feature") —
it is explicitly documented as a description of model behavior, not a
causal or medical claim about any individual food or user.

## 8. Honest limitations of this ML component

- **Dataset size (~105 rows, ~26 per class)** is small. Test-set metrics
  computed on ~27 held-out rows have wide statistical uncertainty — a
  single misclassified example changes accuracy by several percentage
  points. This is disclosed directly in the training metadata
  (`dataset_note` field) and in the UI, not hidden.
- **`meal_type` labels are a simplification**: a real food can be eaten at
  more than one meal; the dataset assigns each food to its single most
  common context (see `ASSUMPTIONS.md`, item 8).
- **No cross-validation** was used (a simple train/test split was used
  instead) because with ~105 rows, k-fold CV would leave very few samples
  per fold per class; this is a reasonable trade-off for a demonstration
  pipeline, not a production-grade evaluation methodology.

## 9. How to retrain with a larger/real dataset

If `data/sample/foods_sample.csv` is replaced with a larger, verified
dataset (see `data/sample/README.md`), simply re-run:

```bash
python -m src.ml.train
```

No other code changes are required — the pipeline reads whatever is
currently seeded in the `foods` table.
