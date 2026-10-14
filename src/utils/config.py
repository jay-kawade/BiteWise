"""
config.py
-------------------------------------------------------------------------------
Central place where the application reads its settings from environment
variables (loaded from a ".env" file if present). Every other module should
import from here instead of calling os.environ directly -- this keeps all
configuration in one, easy-to-find spot.

Beginner note: `python-dotenv`'s `load_dotenv()` reads a ".env" file (if it
exists) and copies its values into the normal OS environment variables, so
`os.getenv(...)` can find them.
-------------------------------------------------------------------------------
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Root of the whole project (two levels up from this file: src/utils/config.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load variables from a .env file in the project root, if it exists.
load_dotenv(PROJECT_ROOT / ".env")


def _get_bool(name: str, default: bool) -> bool:
    """Read an environment variable as a boolean (accepts true/false/1/0)."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# --- Core settings -----------------------------------------------------------

# DEMO_MODE=true means: use only local resources (SQLite, bundled sample
# dataset, locally trained ML model, rule-based assistant fallback). This is
# the default so the app is demonstrable without any API keys.
DEMO_MODE: bool = _get_bool("DEMO_MODE", default=True)

DATABASE_PATH: Path = PROJECT_ROOT / os.getenv("DATABASE_PATH", "data/processed/nutrition_app.db")

SAMPLE_FOODS_CSV: Path = PROJECT_ROOT / "data" / "sample" / "foods_sample.csv"

MODELS_DIR: Path = PROJECT_ROOT / "models"
MEAL_TYPE_MODEL_PATH: Path = MODELS_DIR / "meal_type_classifier.joblib"
MODEL_METADATA_PATH: Path = MODELS_DIR / "meal_type_classifier_metadata.json"

# --- Optional external services ---------------------------------------------

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5").strip()

TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "").strip()

NUTRITION_API_KEY: str = os.getenv("NUTRITION_API_KEY", "").strip()

# --- Derived flags -----------------------------------------------------------

# The conversational assistant only uses a real LLM if the user is NOT forcing
# demo mode AND has actually supplied an API key. Otherwise it uses the
# deterministic, rule-based fallback in src/agent/orchestrator.py.
LLM_ASSISTANT_ENABLED: bool = (not DEMO_MODE) and bool(ANTHROPIC_API_KEY)


def ensure_directories() -> None:
    """Create data/model directories that the app expects to write into."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
