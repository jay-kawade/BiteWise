# Database Schema

Full SQL is in `src/database/schema.sql`. Entity-relationship overview:

```mermaid
erDiagram
    USERS ||--o{ USER_PREFERENCES : has
    USERS ||--o{ NUTRITION_TARGETS : has
    USERS ||--o{ FOOD_LOGS : logs
    USERS ||--o{ SCANNED_FOODS : scans
    USERS ||--o{ MEAL_PLANS : plans
    USERS ||--o{ RECOMMENDATIONS : receives
    USERS ||--o{ FEEDBACK : gives
    FOODS ||--o{ FOOD_LOGS : "referenced by"
    FOODS ||--o{ MEAL_PLAN_ITEMS : "referenced by"
    FOODS ||--o{ RECOMMENDATIONS : "referenced by"
    MEAL_PLANS ||--o{ MEAL_PLAN_ITEMS : contains
    RECOMMENDATIONS ||--o{ FEEDBACK : "rated by"

    USERS {
        int id PK
        text name
        int age
        text sex
        real height_cm
        real weight_kg
        text activity_level
        text goal
        text diet_type
        text cuisine_preference
    }
    USER_PREFERENCES {
        int id PK
        int user_id FK
        text preference_type
        text value
    }
    NUTRITION_TARGETS {
        int id PK
        int user_id FK
        real bmi
        real bmr_kcal
        real tdee_kcal
        real calorie_target_kcal
        real protein_target_g
    }
    FOODS {
        int id PK
        text name
        real calories
        real protein_g
        text dietary_type
        text meal_type
        text allergens
    }
    FOOD_LOGS {
        int id PK
        int user_id FK
        int food_id FK
        text meal_type
        real calories
        text log_date
    }
    SCANNED_FOODS {
        int id PK
        int user_id FK
        text raw_ocr_text
        text parsed_nutrition_json
        real confidence_score
    }
    MEAL_PLANS {
        int id PK
        int user_id FK
        text plan_date
        real target_calories
    }
    MEAL_PLAN_ITEMS {
        int id PK
        int meal_plan_id FK
        text meal_slot
        int food_id FK
    }
    RECOMMENDATIONS {
        int id PK
        int user_id FK
        text context
        int food_id FK
        real score
    }
    FEEDBACK {
        int id PK
        int user_id FK
        int recommendation_id FK
        int rating
    }
```

## Design notes

- **SQLite** was chosen deliberately (Section 22/23 of the original brief):
  it needs no separate server process, ships with Python's standard
  library, and is more than sufficient for a single-user/small-team
  academic demo.
- **Snapshotting in `food_logs`**: nutrition values are copied into the log
  row at logging time (rather than only storing a `food_id` and joining
  live), so a later edit to a food's nutrition data never silently rewrites
  a user's historical log.
- **`ON DELETE CASCADE`** on user-owned tables means removing a user
  profile cleanly removes their preferences/logs/plans — there is no
  orphaned data.
- **Indexes** exist on the columns actually queried by filters in
  `repositories.py` (`meal_type`, `dietary_type`, `(user_id, log_date)`,
  etc.) to keep lookups fast even as the food database or a user's history
  grows.
