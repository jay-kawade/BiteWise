# System Architecture

## 1. High-level module diagram

```mermaid
graph TD
    UI["Streamlit UI (app/)"] --> NUTRI["Nutrition Engine (src/nutrition/)"]
    UI --> ML["ML Pipeline (src/ml/)"]
    UI --> REC["Recommendation Engine (src/recommendation/)"]
    UI --> SCAN["Food Scanner (src/scanner/)"]
    UI --> AGENT["AI Agent Orchestrator (src/agent/)"]
    AGENT --> NUTRI
    AGENT --> ML
    AGENT --> REC
    AGENT --> SCAN
    AGENT --> DB[("SQLite Database\nsrc/database/")]
    NUTRI --> DB
    ML --> DB
    REC --> DB
    SCAN --> DB
    UI --> DB
```

Every arrow into the database goes through `src/database/repositories.py`
— no other module writes raw SQL. This means the storage layer (SQLite)
could be swapped for another database with changes confined to one file.

## 2. Why this architecture

- **Separation of concerns**: nutrition science, ML, recommendation logic,
  OCR, and the UI are independent Python packages under `src/`. Each can
  be tested and explained in isolation (see `tests/`).
- **Single source of truth per number**: the UI never recomputes a
  nutrition value itself — it always calls into `src/nutrition/` or reads
  a stored value from the database. This prevents the classic bug of the
  same number being calculated two different ways on two different pages.
- **The agent is a thin orchestrator, not a calculator**: `src/agent/`
  contains no nutrition math. It only calls functions in `src/agent/tools.py`,
  which themselves call the same modules the UI uses.

## 3. Request flow example — "What should I eat next?"

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit Page
    participant Rec as Recommendation Engine
    participant Nutri as Nutrition Calculator
    participant DB as SQLite Database

    User->>UI: Opens "Recommendations" page
    UI->>DB: get_latest_nutrition_targets(user_id)
    UI->>DB: get_food_logs_for_date(user_id)
    UI->>Nutri: calculate_remaining_targets(targets, consumed)
    Nutri-->>UI: remaining calories / protein
    UI->>Rec: recommend_next_foods(user_id, remaining, diet_type)
    Rec->>DB: search_foods(diet_type, allergens, meal_type)
    DB-->>Rec: candidate foods
    Rec->>Rec: score_food_for_remaining_targets() for each candidate
    Rec-->>UI: ranked ScoredFood list with reasons
    UI-->>User: Shows ranked recommendations with explanations
```

## 4. Deployment view

This is a single-process application: one Python interpreter runs the
Streamlit server, which reads/writes one local SQLite file and loads one
locally-trained model file. There is no separate backend service, no
container orchestration, and no message queue — appropriate for a
student project that must remain fully understandable and runnable on a
laptop (see Section 37 of the original project brief: no
over-engineering).

```mermaid
graph LR
    Browser -->|HTTP/WebSocket| Streamlit["Streamlit Server\n(app/main.py)"]
    Streamlit --> SQLite[("nutrition_app.db")]
    Streamlit --> Model[("meal_type_classifier.joblib")]
    Streamlit -.optional.-> LLM["Anthropic API\n(only if ANTHROPIC_API_KEY set)"]
```
