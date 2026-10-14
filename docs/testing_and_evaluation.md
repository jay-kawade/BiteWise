# Testing & Evaluation

## 1. Automated test suite

Run with:
```bash
pytest
# or, with a coverage report:
pytest --cov=src --cov-report=term-missing
```

As of this writing, the suite contains **85 tests** across:

| File | Covers |
|---|---|
| `tests/test_formulas.py` | BMI/BMR/TDEE/calorie/protein/fat/carb/fiber formulas, boundary values, invalid inputs |
| `tests/test_validation.py` | Profile input validation (age, height, weight, sex, activity, goal, diet type), food log quantity validation |
| `tests/test_database.py` | User CRUD, preferences roundtrip, food search filters (dietary hierarchy, allergen exclusion), empty database, food log CRUD |
| `tests/test_recommender.py` | "What to eat next" respects allergies/diet type, empty database, score ordering, favorite-food bonus |
| `tests/test_meal_planner.py` | Meal-slot share sums to 1.0, one item per slot, honest validation-pass math, missing-target and unknown-user errors |
| `tests/test_substitution.py` | Exact/no-match lookup, original excluded from results, dietary compatibility, score ordering, a targeted regression test for nutrient-similarity quality |
| `tests/test_nutrition_parser.py` | Clean label parsing, OCR-typo fuzzy tolerance, malformed/empty text handling |
| `tests/test_ingredient_parser.py` | Ingredient extraction, controlled-vocabulary allergen detection, user-specific allergy matching, no-false-positive check |
| `tests/test_food_suitability.py` | Diet-type match/mismatch, allergen flagging, high sugar/sodium flags, never uses "healthy"/"unhealthy" language |
| `tests/test_agent_tools.py` | Unknown-user errors, logging, daily consumption totals, medical-advice refusal, graceful handling of unrecognized messages |
| `tests/test_ml_pipeline.py` | Feature engineering correctness, stratified split, metric computation, full training pipeline runs and saves a model |

## 2. Edge cases explicitly covered

- Missing/invalid profile inputs (negative height, out-of-range age, etc.)
- Empty food database (recommendation engine must not crash)
- OCR failure / malformed label text (parser must not crash, must report
  low confidence)
- Unknown ingredient / no allergen match (must not false-positive)
- No suitable food found under current constraints (meal planner / next-
  food engine must report this clearly, not crash or silently substitute)
- Unknown user id passed to any repository/tool function

## 3. Evaluation summary (what is and is not measured)

| Component | Evaluated? | How |
|---|---|---|
| Deterministic nutrition formulas | ✅ Yes | Unit tests check formula arithmetic and internal consistency (e.g. macro calories sum to the calorie target) against the cited equations. |
| ML meal-type classifier | ✅ Yes | Held-out test-set accuracy/precision/recall/F1/confusion matrix, computed live by `src/ml/train.py` and shown in Settings > Model Evaluation. |
| Recommendation / ranking engine | ⚠️ Partially | Ranking logic is unit-tested for correctness (ordering, constraint satisfaction) but formal precision@k/recall@k requires labeled user-preference data, which this project does not have. **Not evaluated due to insufficient validated test data.** |
| OCR / label parsing accuracy | ⚠️ Partially | Parsing logic is unit-tested against known sample text. Real-world OCR accuracy on photographed labels has not been benchmarked against a labeled test set. **Not evaluated due to insufficient validated test data.** |
| System latency | Not formally benchmarked | The app is small enough (single SQLite file, ~105-row dataset, one small trained model) that interactive latency is dominated by Streamlit's own rerun cycle, not by any of this project's algorithms. |

This table itself is shown to the project team via the Settings >
Model Evaluation tab in the running application, per the requirement that
insufficient evaluation must be stated explicitly rather than omitted or
fabricated.
