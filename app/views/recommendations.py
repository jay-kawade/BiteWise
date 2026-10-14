"""
recommendations.py -- "What to eat"

Two tools on one page, both driven by the transparent ranking in
src/recommendation/ranking.py:
  * next-meal suggestions that fit what's left of today's budget
  * swaps: foods with a similar nutrient profile to one you name
"""

import streamlit as st

from app.components.cards import empty_state, food_card, page_header, section, stat
from app.components.disclaimers import render_health_disclaimer
from app.components.session import require_user_id
from app.components.styles import LEAF, PAPRIKA, render_source_badge
from src.database import repositories as repo
from src.nutrition.calculator import calculate_remaining_targets, summarize_consumed
from src.recommendation.recommender import recommend_next_foods
from src.recommendation.substitution import find_food_by_name, find_substitutes


def nums(food) -> str:
    return (f"{food.calories:.0f} kcal &middot; {food.protein_g:.0f} g protein &middot; "
            f"{food.carbohydrates_g:.0f} g carbs &middot; {food.fat_g:.0f} g fat")


page_header("What to eat", "Suggestions ranked against what's left of your day, with the reasons shown.", eyebrow="Plan")
user_id = require_user_id()
user = repo.get_user(user_id)

tab_next, tab_swap = st.tabs(["Next meal", "Find a swap"])

with tab_next:
    targets = repo.get_latest_nutrition_targets(user_id)
    if not targets:
        empty_state("calculate", "No targets yet", "Calculate your targets first so we know what to aim for.")
        st.page_link("views/nutrition_plan.py", label="Go to Targets", icon=":material/arrow_forward:")
    else:
        remaining = calculate_remaining_targets(targets, summarize_consumed(repo.get_food_logs_for_date(user_id)))

        c1, c2, c3 = st.columns([1, 1, 1.2], vertical_alignment="bottom")
        with c1:
            stat("Calories left", f"{remaining['calories']:,.0f}", "kcal", colour=PAPRIKA)
        with c2:
            stat("Protein left", f"{remaining['protein_g']:.0f}", "g", colour=LEAF)
        meal_filter = c3.selectbox("Meal", ["any", "breakfast", "lunch", "dinner", "snack"], format_func=str.capitalize)

        results = recommend_next_foods(
            user_id, remaining["calories"], remaining["protein_g"], user.diet_type,
            meal_type=None if meal_filter == "any" else meal_filter, top_n=8,
        )

        section("Suggestions", f"{len(results)} match{'es' if len(results) != 1 else ''}")
        render_source_badge("rule")
        if not results:
            empty_state("search_off", "Nothing fits right now",
                        "Try another meal filter, or check the restrictions on your profile.")
        left, right = st.columns(2, gap="medium")
        for i, r in enumerate(results):
            with (left if i % 2 == 0 else right):
                food_card(r.food.name, nums(r.food), r.reasons, score=f"{r.score:.2f}")

        if results and st.session_state.get("_logged_recs") != (meal_filter, remaining["calories"]):
            for r in results:
                repo.log_recommendation(user_id, "what_next", r.food.id, r.food.name, r.score, "; ".join(r.reasons))
            st.session_state["_logged_recs"] = (meal_filter, remaining["calories"])

with tab_swap:
    query = st.text_input("Food to replace", placeholder="e.g. paneer")
    if query:
        original = find_food_by_name(query)
        if not original:
            empty_state("search_off", f"We don't have \"{query}\"", "Check the spelling or try a more common name.")
        else:
            st.caption(f"Swaps for **{original.name}** ({original.calories:.0f} kcal, "
                       f"{original.protein_g:.0f} g protein per {original.serving_size_g:.0f} g), "
                       "ranked by how close the nutrients are.")
            substitutes = find_substitutes(original, user_id)
            if not substitutes:
                empty_state("search_off", "No swaps found", "Nothing similar fits your dietary restrictions.")
            left, right = st.columns(2, gap="medium")
            for i, s in enumerate(substitutes):
                with (left if i % 2 == 0 else right):
                    food_card(s.food.name, nums(s.food), s.reasons, score=f"{s.score:.0%} match")
                repo.log_recommendation(user_id, "substitution", s.food.id, s.food.name, s.score, "; ".join(s.reasons))

render_health_disclaimer()
