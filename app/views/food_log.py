"""
food_log.py -- "Food diary"

Search the food database, add servings to a meal, and see today's entries
grouped by meal with running totals.
"""

import streamlit as st

from app.components.cards import empty_state, esc, icon, macro_bar, page_header, section
from app.components.disclaimers import render_health_disclaimer
from app.components.session import require_user_id
from src.database import repositories as repo
from src.database.models import FoodLogEntry
from src.nutrition.calculator import summarize_consumed
from src.nutrition.validation import validate_food_log_quantity

MEALS = ["breakfast", "lunch", "dinner", "snack"]

page_header("Food diary", "Log what you ate. Totals update as you go.", eyebrow="Track")
user_id = require_user_id()

if flash := st.session_state.pop("flash", None):
    st.toast(flash, icon=":material/check:")

entries = repo.get_food_logs_for_date(user_id)
targets = repo.get_latest_nutrition_targets(user_id)

form_col, summary_col = st.columns([1.1, 1], gap="large")

with form_col:
    with st.container(border=True):
        st.markdown("**Add food**")
        query = st.text_input("Search", placeholder="e.g. poha, dal, paneer", label_visibility="collapsed")
        matches = repo.search_foods(query_text=query, dietary_type=None) if query else []

        if query and not matches:
            st.caption(f"Nothing found for \"{query}\". Try a shorter word.")

        selected_food = None
        if matches:
            selected_food = st.selectbox(
                "Food",
                matches,
                format_func=lambda f: f"{f.name}  ·  {f.calories:.0f} kcal / {f.serving_size_g:.0f} g",
            )

        c1, c2 = st.columns(2)
        meal_type = c1.selectbox("Meal", MEALS, format_func=str.capitalize)
        quantity = c2.number_input("Servings", min_value=0.1, max_value=20.0, value=1.0, step=0.5, format="%.1f")

        if selected_food:
            st.caption(
                f"{selected_food.calories * quantity:.0f} kcal · {selected_food.protein_g * quantity:.0f} g protein · "
                f"{selected_food.carbohydrates_g * quantity:.0f} g carbs · {selected_food.fat_g * quantity:.0f} g fat"
            )

        if st.button("Add to diary", type="primary", icon=":material/add:", disabled=selected_food is None):
            errors = validate_food_log_quantity(quantity)
            if errors:
                for e in errors:
                    st.error(e, icon=":material/error:")
            else:
                repo.log_food(FoodLogEntry(
                    id=None, user_id=user_id, food_id=selected_food.id, food_name=selected_food.name,
                    meal_type=meal_type, quantity_servings=quantity,
                    calories=selected_food.calories * quantity, protein_g=selected_food.protein_g * quantity,
                    carbohydrates_g=selected_food.carbohydrates_g * quantity, fat_g=selected_food.fat_g * quantity,
                    fiber_g=selected_food.fiber_g * quantity, sugar_g=selected_food.sugar_g * quantity,
                    sodium_mg=selected_food.sodium_mg * quantity, log_source="database",
                ))
                st.session_state["flash"] = f"Added {selected_food.name} to {meal_type}"
                st.rerun()

with summary_col:
    if targets:
        consumed = summarize_consumed(entries)
        section("Today so far")
        macro_bar("Calories", consumed["calories"], targets.calorie_target_kcal, "kcal")
        macro_bar("Protein", consumed["protein_g"], targets.protein_target_g)
        macro_bar("Carbs", consumed["carbohydrates_g"], targets.carb_target_g)
        macro_bar("Fat", consumed["fat_g"], targets.fat_target_g)

section("Today's entries", f"{len(entries)} logged")

if not entries:
    empty_state("menu_book", "Your diary is empty today", "Search for a food above to add your first entry.")
else:
    for meal in MEALS:
        meal_entries = [e for e in entries if e.meal_type == meal]
        if not meal_entries:
            continue
        meal_kcal = sum(e.calories for e in meal_entries)
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;margin:1rem 0 .3rem;font-weight:600">'
            f'<span>{meal.capitalize()}</span><span style="color:#6F6A60;font-weight:500">{meal_kcal:,.0f} kcal</span></div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            for e in meal_entries:
                c1, c2, c3 = st.columns([4, 2, 0.6], vertical_alignment="center")
                c1.markdown(
                    f'<b>{esc(e.food_name)}</b> <span style="color:#A39D91;font-size:.82rem">'
                    f'&times;{e.quantity_servings:g}{" &middot; " + icon("document_scanner") if e.log_source == "scanned" else ""}</span>',
                    unsafe_allow_html=True,
                )
                c2.markdown(
                    f'<span style="color:#6F6A60;font-size:.88rem">{e.calories:,.0f} kcal &middot; {e.protein_g:.0f} g protein</span>',
                    unsafe_allow_html=True,
                )
                if c3.button("", key=f"del_{e.id}", icon=":material/delete:", type="tertiary", help="Remove entry"):
                    repo.delete_food_log(e.id)
                    st.rerun()

render_health_disclaimer()
