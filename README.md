# BiteWise

**Personalized Nutrition Recommendation and Food Intelligence System**

A final-year academic project (B.Tech Biotechnology, AI/ML minor) that
combines a documented nutrition-science calculator, a genuine machine
learning component, a transparent recommendation engine, a food-label OCR
scanner, and an optional AI assistant into one working application.

> ⚕️ **Disclaimer**: This application provides general nutrition and
> wellness information based on user-provided data. Nutritional values and
> requirements are estimates and may vary by individual. This system is
> not intended to diagnose, treat, or prevent any medical condition and is
> not a substitute for advice from a qualified healthcare professional.

---

## Table of contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Technology stack](#technology-stack)
4. [Installation](#installation)
5. [Running the app](#running-the-app)
6. [Demo mode vs. optional API configuration](#demo-mode-vs-optional-api-configuration)
7. [Project structure](#project-structure)
8. [How the ML component works](#how-the-ml-component-works)
9. [How the recommendation engine works](#how-the-recommendation-engine-works)
10. [How the OCR food scanner works](#how-the-ocr-food-scanner-works)
11. [How the agentic AI layer works](#how-the-agentic-ai-layer-works)
12. [Testing](#testing)
13. [Limitations & ethical considerations](#limitations--ethical-considerations)
14. [Future scope](#future-scope)
15. [Authors](#authors)

---

## Features

- 🧑 **Personalized profile**: personal, lifestyle, goal, diet-type, and
  restriction information.
- 🎯 **Nutrition calculator**: BMI, BMR (Mifflin-St Jeor), TDEE, and
  goal-adjusted calorie/protein/carb/fat/fiber targets — every formula
  documented with its source in `src/nutrition/formulas.py`.
- 🤖 **Real machine learning**: a multi-class classifier (Logistic
  Regression / Decision Tree / Random Forest, compared honestly) that
  predicts a food's likely meal type from its nutrition profile. See
  [How the ML component works](#how-the-ml-component-works).
- 🍽️ **Transparent recommendation engine**: "what should I eat next?",
  full daily meal planning, and nutrient-similarity food substitution —
  all explainable weighted-scoring, not a black box.
- 📷 **Food label scanner**: photo → OpenCV preprocessing → Tesseract OCR
  (with a clearly-labeled mock mode if Tesseract isn't installed) →
  nutrition/ingredient parsing → allergen checking → personalized
  suitability analysis. Verified end-to-end with real Tesseract OCR (see
  [How the OCR food scanner works](#how-the-ocr-food-scanner-works)).
- 📒 **Daily food tracker** with progress bars against your targets.
- 📈 **Weekly analytics** with simple, transparent insights.
- 🎨 **Custom UI**: a BiteWise theme (`.streamlit/config.toml`) with
  Fraunces + DM Sans type, a warm food-inspired palette, a hand-drawn SVG
  logo (`app/assets/`), and shared components in `app/components/` (stat
  tiles, macro bars, food lists, nutrition-facts panel). Icons are Google
  Material Symbols, no emoji.
- 🤖 **AI Nutrition Assistant**: works out of the box with a rule-based
  intent router (no API key needed), or becomes a full LLM tool-using
  agent if you configure `ANTHROPIC_API_KEY`.
- 🔒 **Safety by design**: no diagnosis/treatment claims, no universal
  "healthy/unhealthy" labels, no fabricated data or metrics — enforced
  throughout the codebase, not just described in this README.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for full diagrams. In
short: a Streamlit UI (`app/`) calls into independent, testable Python
packages under `src/` (nutrition, ml, recommendation, scanner, agent,
database). Every arrow into storage goes through
`src/database/repositories.py`.

## Technology stack

| Layer | Choice | Why |
|---|---|---|
| UI | Streamlit | Fast to build a clean multi-page data app in pure Python — appropriate for a non-CS team. |
| Database | SQLite | Zero-configuration, file-based, ships with Python. |
| ML | scikit-learn | Industry-standard, well-documented, easy to explain (Pipeline + ColumnTransformer). |
| OCR | Tesseract (via pytesseract) + OpenCV | Free, open-source, runs fully locally. |
| Charts | Plotly | Clean interactive charts inside Streamlit. |
| Optional LLM | Anthropic API | Only used if you provide a key; the app is fully functional without it. |

## Installation

**Python version**: 3.10 - 3.13 (developed and tested on 3.13).

```bash
# 1. Clone / open this project folder, then create a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. (Optional but recommended) install the Tesseract OCR engine for real
#    label scanning. Without it, the scanner runs in a clearly-labeled
#    mock mode so the rest of the app still works.
#    macOS:   brew install tesseract
#    Ubuntu:  sudo apt-get install tesseract-ocr
#    Windows: https://github.com/UB-Mannheim/tesseract/wiki

# 4. Copy the environment template (defaults already work for a full local demo)
cp .env.example .env
```

### Dataset setup

Nothing to do — a demo food dataset (`data/sample/foods_sample.csv`, ~105
common foods, clearly labeled as developer-compiled reference data) is
bundled and gets loaded into the database automatically the first time
you run the app. See `data/sample/README.md` for exactly how to replace it
with a real, verified dataset later.

### Database setup

Also automatic — `app/main.py` calls `src/database/seed.py::ensure_seeded()`
on first run, which creates `data/processed/nutrition_app.db` and loads the
demo foods into it. To reset the database, simply delete that file.

### ML training

Also automatic on first run (the app trains and saves a model if none
exists yet). To retrain manually at any time:

```bash
python -m src.ml.train
```

This prints the comparison of all candidate models and saves the best one
(by macro-F1) to `models/meal_type_classifier.joblib`.

## Running the app

```bash
streamlit run app/main.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).
First launch: open **Profile** (under "You" in the sidebar) and create a profile — every
other page needs one active profile to show data for.

## Demo mode vs. optional API configuration

By default (`.env` → `DEMO_MODE=true`), everything runs 100% locally:
SQLite database, bundled food dataset, locally-trained ML model, and a
rule-based AI assistant fallback. **No API key is required to demonstrate
every feature of this project.**

To enable a more conversational AI assistant (optional):
```bash
# in .env
DEMO_MODE=false
ANTHROPIC_API_KEY=sk-ant-...
```
If the key is invalid/unreachable at runtime, the app automatically falls
back to the rule-based assistant rather than crashing (see
`src/agent/orchestrator.py`).

## Project structure

```
personalized-nutrition/
├── app/                    Streamlit UI
│   ├── main.py             Entry point, navigation, bootstrap
│   ├── views/               One file per screen
│   └── components/          Shared styling, cards, disclaimers, session state
├── src/
│   ├── nutrition/           Deterministic formulas, calculator, validation, suitability analysis
│   ├── ml/                  Preprocessing, training, evaluation, inference
│   ├── recommendation/      Ranking, "what next", meal planner, substitution
│   ├── scanner/             Image preprocessing, OCR, nutrition/ingredient parsing
│   ├── agent/                Tool functions, orchestrator, safety prompts
│   ├── database/            SQLite schema, models, repositories, seeding
│   └── utils/                Config, logging
├── data/
│   ├── raw/                  Where a real dataset would go
│   ├── processed/            Generated database / training data (git-ignored)
│   └── sample/                Bundled demo food dataset + generator script
├── models/                    Trained model + metadata (git-ignored)
├── tests/                     pytest test suite (85 tests)
├── docs/                      Architecture, methodology, schema, testing docs
├── ASSUMPTIONS.md             Every documented design assumption
├── requirements.txt
├── .env.example
└── README.md                  You are here
```

## How the ML component works

**Task**: multi-class classification — predict a food's most likely
`meal_type` (breakfast/lunch/dinner/snack) from its per-100g-normalized
nutrition profile. Three models (Logistic Regression, Decision Tree,
Random Forest) are trained behind an identical preprocessing pipeline and
compared on a held-out test set using accuracy/precision/recall/F1/
confusion matrix; the highest macro-F1 model is selected automatically.
Full justification, honesty about dataset-size limitations, and
explainability details are in
[`docs/ml_methodology.md`](docs/ml_methodology.md).

This is used to auto-suggest a meal type for a newly scanned/added food —
it is always shown separately from calculated or rule-based numbers in the
UI (look for the "ML Prediction" badge).

## How the recommendation engine works

Transparent weighted scoring, not a trained model:
- **"What should I eat next?"** scores each candidate food on calorie fit,
  protein fit, macro balance, and preference match against your
  *remaining* daily targets.
- **Meal planner** allocates your daily targets across 5 meal slots and
  greedily picks the best-fitting food for each slot, then validates the
  total against your target.
- **Substitution** ranks candidate replacement foods by nutrient-profile
  cosine similarity (normalized so no single nutrient dominates) plus
  meal-context compatibility.

Full details: [`src/recommendation/ranking.py`](src/recommendation/ranking.py)
(heavily commented) and `ASSUMPTIONS.md`.

## How the OCR food scanner works

```
photo → OpenCV preprocessing → Tesseract OCR (or labeled mock mode)
      → regex + fuzzy-match nutrition parsing → ingredient extraction
      → controlled-vocabulary + user-specific allergen checking
      → personalized suitability analysis
```

If Tesseract isn't installed, the app clearly labels results as coming
from **mock mode** using a sample label — it never pretends a mock result
is a real scan. See [`docs/data_flow.md`](docs/data_flow.md).

**Verified working end-to-end**: with Tesseract installed
(`brew install tesseract`), a synthetically rendered nutrition label was
run through the full pipeline and correctly extracted all 9 nutrition
fields (calories, protein, carbs, fat, saturated fat, fiber, sugar,
sodium, serving size) at 94.5% OCR confidence, correctly split a
multi-line ingredient list, and correctly flagged all 4 real allergens
present (milk, gluten, peanut, soy) against the controlled allergen
vocabulary.

## How the agentic AI layer works

`src/agent/tools.py` exposes a fixed set of functions (get profile, get
targets, search foods, log food, generate meal plan, suggest
substitutions, get weekly summary, analyze a scanned label, ...). The
orchestrator (`src/agent/orchestrator.py`) either:
1. Routes your message through a transparent, readable keyword→tool
   mapping (default, no API key needed), or
2. Lets a real LLM (Anthropic, tool-use) decide which tools to call, if
   you configure an API key.

**In both modes, the agent never calculates a nutrition number itself —
it can only call the same deterministic/ML/recommendation functions the
rest of the app uses.** Medical-advice questions (medication, diagnosis,
treatment) are intercepted by a keyword safety net before either mode
runs, and answered with a refusal that points to a qualified professional.

## Testing

```bash
pytest                                   # run all 85 tests
pytest --cov=src --cov-report=term-missing   # with coverage
pytest tests/test_formulas.py -v          # run one file
```

See [`docs/testing_and_evaluation.md`](docs/testing_and_evaluation.md) for
what is covered, including edge cases, and an honest statement of what
has and has not been formally evaluated.

## Limitations & ethical considerations

See [`docs/limitations_and_future_scope.md`](docs/limitations_and_future_scope.md)
for the full, honest list (small demo dataset, unverified OCR accuracy on
real photos, no cross-contamination detection, population-level formula
estimates, etc.) and the ethical safeguards built into the system.

## Future scope

See [`docs/limitations_and_future_scope.md`](docs/limitations_and_future_scope.md#future-scope).

## Authors

_Add your team's names and roles here before submission._

- Student Name 1 — Role (e.g. Nutrition logic, formulas)
- Student Name 2 — Role (e.g. ML pipeline)
- Student Name 3 — Role (e.g. Scanner / OCR)
- Student Name 4 — Role (e.g. UI / integration)

---

## Quick command reference

```bash
# Install
pip install -r requirements.txt

# Run the app (auto-initializes DB + trains ML model on first run)
streamlit run app/main.py

# Retrain the ML model manually
python -m src.ml.train

# Regenerate the demo food dataset CSV (rarely needed)
python data/sample/generate_sample_foods.py

# Run tests
pytest
```
