"""
food_analysis.py -- "Check a food"

Same suitability check the scanner uses, but for a food that's already in
the database or for numbers typed in by hand.
"""

import streamlit as st

from app.components.cards import checklist, page_header, section, stat, tag
from app.components.disclaimers import render_health_disclaimer
from app.components.session import require_user_id
from app.components.styles import LEAF, PAPRIKA, PLUM, SAFFRON
from src.database import repositories as repo
from src.nutrition.calculator import calculate_remaining_targets, summarize_consumed
from src.nutrition.food_suitability import analyze_food_suitability

page_header("Check a food", "Is it a good fit for you right now? Pick something from the database or type in the numbers.",
            eyebrow="Track")
user_id = require_user_id()
user = repo.get_user(user_id)

targets = repo.get_latest_nutrition_targets(user_id)
remaining = None
if targets:
    remaining = calculate_remaining_targets(targets, summarize_consumed(repo.get_food_logs_for_date(user_id)))


def run_check(nutrition, food_dietary_type=None, allergy_warnings=()):
    return analyze_food_suitability(
        nutrition=nutrition, diet_type=user.diet_type, food_dietary_type=food_dietary_type,
        food_allergen_warnings=list(allergy_warnings),
        remaining_calorie_budget=remaining["calories"] if remaining else None,
        remaining_protein_budget=remaining["protein_g"] if remaining else None,
    )


tab_db, tab_manual = st.tabs(["From the database", "Enter manually"])

with tab_db:
    query = st.text_input("Search", placeholder="Search foods, e.g. idli", label_visibility="collapsed",
                          key="analyzer_search")
    matches = repo.search_foods(query_text=query) if query else []

    if query and not matches:
        st.caption(f"Nothing found for \"{query}\".")

    if matches:
        food = st.selectbox("Food", matches, format_func=lambda f: f.name, label_visibility="collapsed")

        st.markdown(
            f'<div style="margin:.4rem 0 1rem">{tag(food.category)}{tag(food.cuisine)}'
            f'{tag(food.dietary_type.replace("_", "-"), "green")}{tag(f"{food.serving_size_g:.0f} g serving")}</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            stat("Energy", f"{food.calories:.0f}", "kcal", colour=PAPRIKA)
        with c2:
            stat("Protein", f"{food.protein_g:.0f}", "g", colour=LEAF)
        with c3:
            stat("Carbs", f"{food.carbohydrates_g:.0f}", "g", colour=SAFFRON)
        with c4:
            stat("Fat", f"{food.fat_g:.0f}", "g", colour=PLUM)

        restricted = {a.lower() for a in repo.get_preference_values(user_id, "allergy")}
        restricted |= {a.lower() for a in repo.get_preference_values(user_id, "avoid_ingredient")}
        allergy_warnings = [
            f"Contains {a}, which is on your restricted list" for a in food.allergen_list() if a.lower() in restricted
        ]

        result = run_check(
            {
                "calories": food.calories, "protein_g": food.protein_g, "carbohydrates_g": food.carbohydrates_g,
                "fat_g": food.fat_g, "sugar_g": food.sugar_g, "sodium_mg": food.sodium_mg,
            },
            food_dietary_type=food.dietary_type,
            allergy_warnings=allergy_warnings,
        )
        section(f"How {food.name} fits")
        checklist(result.checklist, verdict=result.suitability_label)

with tab_manual:
    with st.form("manual_analysis_form", border=False):
        st.caption("Per serving, as printed on the pack.")
        c1, c2, c3 = st.columns(3)
        calories = c1.number_input("Calories (kcal)", min_value=0.0, value=200.0)
        protein_g = c1.number_input("Protein (g)", min_value=0.0, value=10.0)
        carbs_g = c2.number_input("Carbohydrates (g)", min_value=0.0, value=25.0)
        fat_g = c2.number_input("Fat (g)", min_value=0.0, value=8.0)
        sugar_g = c3.number_input("Sugar (g)", min_value=0.0, value=5.0)
        sodium_mg = c3.number_input("Sodium (mg)", min_value=0.0, value=200.0)
        analyze_clicked = st.form_submit_button("Check it", type="primary")

    if analyze_clicked:
        result = run_check({
            "calories": calories, "protein_g": protein_g, "carbohydrates_g": carbs_g,
            "fat_g": fat_g, "sugar_g": sugar_g, "sodium_mg": sodium_mg,
        })
        section("How it fits")
        checklist(result.checklist, verdict=result.suitability_label)

render_health_disclaimer()
