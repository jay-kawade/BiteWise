# data/processed/

Generated at runtime / by scripts. Nothing here is source-controlled (see
`.gitignore`) except this README.

Contents created when you run the app or the ML pipeline:

- `nutrition_app.db` -- the SQLite database (created by `src/database/db.py`
  the first time the app runs; seeded from `data/sample/foods_sample.csv`
  by `src/database/seed.py`).
- `ml_training_data.csv` -- the cleaned, feature-engineered table used to
  train the meal-type classifier (created by `src/ml/preprocessing.py`).
