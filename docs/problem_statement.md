# Problem Statement, Objectives & Requirements

## 1. Problem Statement

Making informed, personalized food choices requires combining several
pieces of information that are usually scattered across different tools:
a person's own body/lifestyle data, standard nutrition science formulas,
information about the specific foods available to them (including
packaged foods with printed nutrition labels), and their own dietary
history. Most consumer nutrition apps either (a) reduce this to a manual
calorie-counting spreadsheet with no personalization, or (b) make
unsupported medical/health claims. There is a need for a system that
combines deterministic nutrition science, genuine data-driven
classification, transparent recommendation logic, and food-label
intelligence into one coherent tool, while remaining scientifically
honest about what it can and cannot claim.

## 2. Objectives

1. Build a user nutrition profile from health/lifestyle parameters.
2. Estimate nutrition requirements using documented, cited formulas.
3. Build and evaluate a genuine machine learning component for a
   well-defined, honestly-evaluable task.
4. Build a transparent recommendation engine for meal suggestions,
   substitutions, and meal planning.
5. Build a food-label scanning pipeline (image → OCR → parsing →
   ingredient/allergen analysis).
6. Track daily food intake and compare it against personalized targets.
7. Provide an (optional) natural-language assistant that orchestrates all
   of the above through explicit tool calls, never by inventing numbers.
8. Do all of this while remaining scientifically responsible: no
   diagnosis, treatment claims, or fabricated data/metrics.

## 3. Proposed Solution

A modular Python application (Streamlit UI + a `src/` library of
independent modules for nutrition calculation, ML, recommendation,
scanning, database access, and an agent/orchestrator layer). Every
"number" the user sees is traceable to exactly one of three sources,
which the UI labels explicitly:

- **Calculated** — deterministic formulas (`src/nutrition/formulas.py`)
- **ML Prediction** — the trained meal-type classifier (`src/ml/`)
- **Rule-Based** — the transparent scoring/ranking engine
  (`src/recommendation/ranking.py`)

## 4. Functional Requirements

- FR1: Create/edit a user profile with personal, lifestyle, goal, diet,
  preference, and restriction information.
- FR2: Calculate BMI, BMR, TDEE, and goal-adjusted calorie/macro targets.
- FR3: Train and use an ML model to classify a food's likely meal type
  from its nutrition profile.
- FR4: Search/filter the food database by diet type, meal type, calories,
  and allergen exclusions.
- FR5: Scan a nutrition label image and extract structured nutrition
  values and an ingredient list via OCR.
- FR6: Detect potential allergen/ingredient matches against user-declared
  restrictions.
- FR7: Analyze any food (scanned or selected) against the user's profile
  and remaining daily targets.
- FR8: Log foods against meal slots and track daily consumption vs.
  targets.
- FR9: Recommend foods to eat next based on remaining daily targets.
- FR10: Generate a full daily meal plan and validate it against targets.
- FR11: Suggest nutrient-similar substitutes for a given food.
- FR12: Summarize weekly nutrition trends and simple, transparent
  insights.
- FR13: Provide a conversational assistant that can call the above
  capabilities as tools, with a rule-based fallback requiring no API key.

## 5. Non-Functional Requirements

- NFR1 (Usability): runnable and demonstrable with zero external API keys
  or paid services (`DEMO_MODE=true`).
- NFR2 (Maintainability): clear separation of concerns across `src/`
  submodules; no single file mixes UI, business logic, and data access.
- NFR3 (Explainability): every ML prediction is shown with a confidence
  score and, for the underlying model, global feature importance.
- NFR4 (Safety): the system must never present itself as a diagnostic or
  treatment tool (see `docs/limitations_and_future_scope.md` and the
  in-app Settings > Safety tab).
- NFR5 (Performance): the ML model and food dataset are loaded once per
  server process (`st.cache_resource`), not recomputed per interaction.
- NFR6 (Testability): core logic (formulas, validation, recommendation
  ranking, parsing, database operations, agent tools) is covered by
  automated pytest tests independent of the UI.
