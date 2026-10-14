# ASSUMPTIONS.md

This file documents every design decision made where the underlying
literature/guidelines allow a *range* rather than one fixed number, or
where a simplifying, non-medical assumption was needed to build a working
system. Nothing in this file invents a scientific fact -- every number
below is either a documented midpoint/typical value from a cited source
(see `src/nutrition/formulas.py`) or an explicit modeling simplification.

## Nutrition formulas (`src/nutrition/formulas.py`)

1. **BMR for `sex = "other"`**: The Mifflin-St Jeor equation was validated
   using a binary male/female variable. For a user who selects "other",
   this app uses the mathematical average of the male and female formula
   results. This is a pragmatic, documented approximation -- not a claim
   that it is scientifically validated for all individuals.

2. **Protein target (g/kg body weight) by goal**: The ISSN Position Stand
   on protein supports a broad range of ~1.4-2.0 g/kg/day for active
   individuals, and the IOM RDA baseline is 0.8 g/kg/day for sedentary
   adults. This app picks specific values within/near that range:
   `maintenance=1.2, weight_loss=1.6, weight_gain=1.4, muscle_gain=1.8`
   g/kg. These are reasonable defaults, not individualized prescriptions.

3. **Fat target = 27% of total calories**: The Acceptable Macronutrient
   Distribution Range (AMDR) for fat is 20-35% of calories. 27% (roughly
   the midpoint) was chosen as a single default so the app can always
   produce one calorie/macro plan rather than a range.

4. **Fiber target = 14g per 1000 kcal**: This is a commonly cited Adequate
   Intake (AI) guideline reference point, used directly (not a range that
   needed picking).

5. **Calorie adjustment for goals**: A 500 kcal/day deficit/surplus for
   weight_loss/weight_gain, and a smaller 300 kcal/day surplus for
   muscle_gain (to favor lean mass gain over fat gain, a common practical
   recommendation). The underlying "500 kcal ≈ 0.45 kg/week" rule is a
   long-standing approximation, not a precise physiological law -- this is
   disclosed in the UI and in `formulas.py`.

6. **Minimum safe calorie floor = 1200 kcal/day**: A commonly cited general
   floor for adults in mainstream dietary guidance, used to prevent the app
   from ever recommending an unsafely low calorie target regardless of
   goal/TDEE inputs.

## Recommendation engine (`src/recommendation/`)

7. **Meal-slot calorie allocation for the daily meal planner**: breakfast
   25%, mid-morning snack 10%, lunch 30%, evening snack 10%, dinner 25% of
   the daily calorie target. This is a simple, commonly used 5-meal
   distribution pattern chosen for demonstration purposes -- not derived
   from a specific cited study.

8. **A food's `meal_type` in the demo dataset** represents the single most
   common meal context for that food (e.g. "Idli" -> breakfast), even
   though many foods can realistically be eaten at more than one meal.
   This simplification was necessary to (a) let the food database support
   meal-type filtering and (b) provide a clean classification target for
   the ML model (Section 5 of the original spec).

9. **Nutrient-similarity reference scale for substitutions**
   (`src/recommendation/ranking.py::_REFERENCE_SCALE`): calories, protein,
   carbs, fat, fiber, sugar, and sodium are each divided by a typical
   reference value before computing cosine similarity, specifically so
   that no single nutrient (calories, which is numerically much larger
   than the others) dominates the similarity score. The reference values
   were chosen to bring all features into a comparable numeric range, and
   were validated by checking that a known-sensible substitution (tofu for
   paneer, both protein/fat-dense) outranks a known-poor one (roti, a
   carb-dense staple) -- see `tests/test_substitution.py`.

## Machine learning (`src/ml/`)

10. **ML task = classifying a food's `meal_type` from its nutrition
    profile**: chosen because it uses a real column already in the food
    database (not a fabricated label), is genuinely useful (auto-suggesting
    a meal slot for a newly added or scanned food), and is honestly
    evaluable with standard classification metrics. See
    `docs/ml_methodology.md` for the full justification.

11. **Dataset size**: the bundled demo dataset has ~105 food rows. This is
    large enough to demonstrate a real train/test split and model
    comparison, but too small for high-confidence production accuracy
    claims. This is disclosed directly in the training script's metadata
    output and in the Settings > Model Evaluation page, not hidden.

## Scanner (`src/scanner/`)

12. **OCR mock mode**: when the Tesseract OCR engine is not installed on
    the machine, the scanner returns one of two clearly-labeled sample
    nutrition-label texts instead of failing. Every result carries an
    explicit `mode` field ("real" or "mock") shown in the UI, so a mock
    result is never presented as if it came from a real scan.

13. **Fuzzy OCR-typo tolerance threshold = 82/100** (rapidfuzz partial
    ratio): chosen as a threshold high enough to catch common single/double
    -character OCR mistakes (e.g. "Proteln" for "Protein") while remaining
    unlikely to match a genuinely unrelated word. Any fuzzy match is always
    flagged to the user as a warning to verify.

## UI page consolidation (`app/`)

15. The original 13-screen list (Section 20 of the brief) is implemented
    as **11 navigation pages** by combining closely related screens that
    share the same engine and would otherwise duplicate UI code:
    - "Landing/Home" and "Dashboard" are combined into one Dashboard page
      (the dashboard itself serves as the landing screen, and prompts
      first-time users to the Profile page if no profile exists yet).
    - "What should I eat next?" and "Food substitution" are combined into
      one **Recommendations** page (as two tabs), since both are powered
      by the same transparent ranking engine (`src/recommendation/ranking.py`).
    - "Food analysis result" is generalized into a standalone **Food
      Analyzer** page that can analyze either a scanned food or any food
      picked from the database/entered manually, rather than only being
      reachable right after a scan.
    This keeps the codebase from having two near-duplicate pages while
    still covering every required capability.

## Database & profile (`src/database/`)

14. **No authentication system**: this is a single-machine academic demo
    with a lightweight "active profile" selector (no passwords/accounts),
    per the "no unnecessary auth systems" guidance for a student project.
    Multiple profiles can still be created and switched between for demo
    purposes.
