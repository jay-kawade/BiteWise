"""
BiteWise -- Streamlit entry point.

    streamlit run app/main.py

On first start this seeds the food database and trains the meal-type
classifier if no saved model exists (cached with st.cache_resource, so it
only happens once per server process). Then it sets up the theme, sidebar
and page navigation.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.components.session import render_user_selector_sidebar  # noqa: E402
from app.components.styles import inject_custom_css  # noqa: E402
from src.database.seed import ensure_seeded  # noqa: E402
from src.ml.predict import is_model_available  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)
ASSETS = Path(__file__).resolve().parent / "assets"

st.set_page_config(
    page_title="BiteWise",
    page_icon=str(ASSETS / "bitewise_mark.svg"),
    layout="wide",
)


@st.cache_resource
def bootstrap_app():
    """Runs exactly once per running server process (Streamlit caches the result)."""
    ensure_seeded()
    if not is_model_available():
        logger.info("No trained ML model found -- training the meal-type classifier now (first run only).")
        from src.ml.train import train_and_select_best_model
        train_and_select_best_model()
    return True


bootstrap_app()
inject_custom_css()

st.logo(str(ASSETS / "bitewise_logo.svg"), icon_image=str(ASSETS / "bitewise_mark.svg"), size="large")
render_user_selector_sidebar()

pages = {
    "": [
        st.Page("views/dashboard.py", title="Today", icon=":material/today:", default=True),
        st.Page("views/assistant.py", title="Ask BiteWise", icon=":material/forum:"),
    ],
    "Track": [
        st.Page("views/food_log.py", title="Food diary", icon=":material/menu_book:"),
        st.Page("views/scanner.py", title="Scan a label", icon=":material/document_scanner:"),
        st.Page("views/food_analysis.py", title="Check a food", icon=":material/manage_search:"),
    ],
    "Plan": [
        st.Page("views/recommendations.py", title="What to eat", icon=":material/restaurant:"),
        st.Page("views/meal_plan.py", title="Meal plan", icon=":material/event_note:"),
        st.Page("views/analytics.py", title="Your week", icon=":material/bar_chart:"),
    ],
    "You": [
        st.Page("views/nutrition_plan.py", title="Targets", icon=":material/track_changes:"),
        st.Page("views/profile.py", title="Profile", icon=":material/person:"),
        st.Page("views/settings.py", title="About & model", icon=":material/info:"),
    ],
}

navigation = st.navigation(pages)
navigation.run()
