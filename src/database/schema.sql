-- ==============================================================================
-- schema.sql
-- SQLite schema for the Personalized Nutrition Recommendation and Food
-- Intelligence System.
--
-- Design notes:
--   * SQLite is used because it needs no separate server -- perfect for a
--     student project that must run on any laptop with just Python.
--   * We deliberately do NOT store unnecessary sensitive personal data
--     (no exact address, no national ID, no raw medical records). Health
--     condition notes, if any, are free-text and clearly optional.
--   * Foreign keys with ON DELETE CASCADE keep related rows (preferences,
--     logs, plans) consistent if a user is ever removed.
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------------
-- users: the core profile (Section 3 of the requirements)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    name                        TEXT NOT NULL,
    age                         INTEGER NOT NULL,
    sex                         TEXT NOT NULL CHECK (sex IN ('male', 'female', 'other')),
    height_cm                   REAL NOT NULL,
    weight_kg                   REAL NOT NULL,
    activity_level              TEXT NOT NULL DEFAULT 'moderately_active',
    exercise_frequency_per_week INTEGER NOT NULL DEFAULT 0,
    exercise_type               TEXT DEFAULT '',
    sleep_hours                 REAL DEFAULT 7.0,
    goal                        TEXT NOT NULL DEFAULT 'maintenance'
                                CHECK (goal IN ('weight_loss', 'maintenance', 'weight_gain', 'muscle_gain')),
    diet_type                   TEXT NOT NULL DEFAULT 'vegetarian'
                                CHECK (diet_type IN ('vegan', 'vegetarian', 'eggetarian', 'non_vegetarian')),
    cuisine_preference          TEXT DEFAULT 'indian',
    budget_preference           TEXT DEFAULT 'medium',
    cooking_time_preference     TEXT DEFAULT 'medium',
    meals_per_day               INTEGER NOT NULL DEFAULT 4,
    health_notes                TEXT DEFAULT '',
    created_at                  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at                  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------------
-- user_preferences: favorite/disliked foods, allergies, ingredients to avoid
-- One row per preference item, so a user can have many of each type.
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_preferences (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preference_type TEXT NOT NULL CHECK (
                        preference_type IN ('favorite_food', 'disliked_food', 'allergy', 'avoid_ingredient')
                    ),
    value           TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id);

-- ------------------------------------------------------------------
-- nutrition_targets: the output of the deterministic nutrition calculator
-- (Section 4). One row per calculation, so history is preserved.
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nutrition_targets (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bmi                 REAL NOT NULL,
    bmi_category        TEXT NOT NULL,
    bmr_kcal            REAL NOT NULL,
    tdee_kcal           REAL NOT NULL,
    calorie_target_kcal REAL NOT NULL,
    protein_target_g    REAL NOT NULL,
    carb_target_g       REAL NOT NULL,
    fat_target_g        REAL NOT NULL,
    fiber_target_g      REAL NOT NULL,
    calculated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_nutrition_targets_user ON nutrition_targets(user_id);

-- ------------------------------------------------------------------
-- foods: the food/nutrition database (Section 7)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS foods (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    category         TEXT NOT NULL,
    serving_size_g   REAL NOT NULL,
    calories         REAL NOT NULL,
    protein_g        REAL NOT NULL,
    carbohydrates_g  REAL NOT NULL,
    fat_g            REAL NOT NULL,
    fiber_g          REAL NOT NULL DEFAULT 0,
    sugar_g          REAL NOT NULL DEFAULT 0,
    sodium_mg        REAL NOT NULL DEFAULT 0,
    saturated_fat_g  REAL NOT NULL DEFAULT 0,
    dietary_type     TEXT NOT NULL CHECK (dietary_type IN ('vegan', 'vegetarian', 'eggetarian', 'non_vegetarian')),
    meal_type        TEXT NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    cuisine          TEXT DEFAULT 'other',
    allergens        TEXT DEFAULT '',
    tags             TEXT DEFAULT '',
    source           TEXT NOT NULL DEFAULT 'demo_reference'
);

CREATE INDEX IF NOT EXISTS idx_foods_meal_type ON foods(meal_type);
CREATE INDEX IF NOT EXISTS idx_foods_dietary_type ON foods(dietary_type);
CREATE INDEX IF NOT EXISTS idx_foods_name ON foods(name);

-- ------------------------------------------------------------------
-- food_logs: daily food tracker entries (Section 11)
-- Nutrition values are stored as a *snapshot* at logging time so that later
-- edits to the foods table do not silently rewrite a user's history.
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS food_logs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    food_id           INTEGER REFERENCES foods(id) ON DELETE SET NULL,
    food_name         TEXT NOT NULL,
    meal_type         TEXT NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    quantity_servings REAL NOT NULL DEFAULT 1.0,
    calories          REAL NOT NULL,
    protein_g         REAL NOT NULL,
    carbohydrates_g   REAL NOT NULL,
    fat_g             REAL NOT NULL,
    fiber_g           REAL NOT NULL DEFAULT 0,
    sugar_g           REAL NOT NULL DEFAULT 0,
    sodium_mg         REAL NOT NULL DEFAULT 0,
    log_source        TEXT NOT NULL DEFAULT 'manual' CHECK (log_source IN ('manual', 'scanned', 'database')),
    logged_at         TEXT NOT NULL DEFAULT (datetime('now')),
    log_date          TEXT NOT NULL DEFAULT (date('now'))
);

CREATE INDEX IF NOT EXISTS idx_food_logs_user_date ON food_logs(user_id, log_date);

-- ------------------------------------------------------------------
-- scanned_foods: results of the OCR food-label scanner (Section 8)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scanned_foods (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id               INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    raw_ocr_text          TEXT DEFAULT '',
    parsed_nutrition_json TEXT DEFAULT '{}',
    parsed_ingredients_json TEXT DEFAULT '[]',
    allergen_warnings_json TEXT DEFAULT '[]',
    confidence_score      REAL DEFAULT 0.0,
    ocr_mode              TEXT DEFAULT 'mock',
    created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_scanned_foods_user ON scanned_foods(user_id);

-- ------------------------------------------------------------------
-- meal_plans / meal_plan_items (Section 13)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS meal_plans (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_date        TEXT NOT NULL DEFAULT (date('now')),
    plan_type        TEXT NOT NULL DEFAULT 'daily' CHECK (plan_type IN ('daily', 'weekly')),
    target_calories  REAL NOT NULL,
    target_protein_g REAL NOT NULL,
    total_calories   REAL NOT NULL DEFAULT 0,
    total_protein_g  REAL NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS meal_plan_items (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_plan_id      INTEGER NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    meal_slot         TEXT NOT NULL,
    food_id           INTEGER REFERENCES foods(id) ON DELETE SET NULL,
    food_name         TEXT NOT NULL,
    quantity_servings REAL NOT NULL DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_meal_plan_items_plan ON meal_plan_items(meal_plan_id);

-- ------------------------------------------------------------------
-- recommendations: a log of what the recommendation engine suggested, so it
-- can be reviewed/evaluated and so feedback can reference it (Section 32)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recommendations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    context    TEXT NOT NULL CHECK (context IN ('what_next', 'substitution', 'meal_plan')),
    food_id    INTEGER REFERENCES foods(id) ON DELETE SET NULL,
    food_name  TEXT NOT NULL,
    score      REAL NOT NULL,
    reason     TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_recommendations_user ON recommendations(user_id);

-- ------------------------------------------------------------------
-- feedback: lets a user rate a recommendation (used for future personalization)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recommendation_id INTEGER REFERENCES recommendations(id) ON DELETE SET NULL,
    rating            INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment           TEXT DEFAULT '',
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
