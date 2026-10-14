"""
meal_plan.py -- "Meal plan"

Builds a five-slot day (breakfast, mid-morning, lunch, evening snack,
dinner) with the rule-based planner, then checks the totals against the
user's targets.
"""

from datetime import date

import streamlit as st

from app.components.cards import empty_state, food_card, page_header, section, stat
from app.components.disclaimers import render_health_disclaimer
from app.components.session import require_user_id
from app.components.styles import LEAF, PAPRIKA, render_source_badge
from src.database import repositories as repo
from src.database.models import MealPlan, MealPlanItem
from src.recommendation.meal_planner import generate_daily_meal_plan

SLOT_TIMES = {
    "breakfast": "8:00",
    "mid_morning_snack": "11:00",
    "lunch": "13:30",
    "evening_snack": "17:00",
    "dinner": "20:30",
}

page_header("Meal plan", "A full day of meals sized to your targets. Don't like it? Generate another.", eyebrow="Plan")
user_id = require_user_id()

targets = repo.get_latest_nutrition_targets(user_id)
if not targets:
    empty_state("calculate", "No targets yet", "We need your daily targets before we can plan a day.")
    st.page_link("views/nutrition_plan.py", label="Go to Targets", icon=":material/arrow_forward:")
    st.stop()

plan = st.session_state.get("last_meal_plan")

if st.button("Plan my day" if plan is None else "Make a new plan", type="primary", icon=":material/refresh:"):
    plan = generate_daily_meal_plan(user_id)
    st.session_state["last_meal_plan"] = plan
    repo.save_meal_plan(MealPlan(
        id=None, user_id=user_id, plan_date=str(date.today()), plan_type="daily",
        target_calories=plan.target_calories, target_protein_g=plan.target_protein_g,
        total_calories=plan.total_calories, total_protein_g=plan.total_protein_g,
        items=[
            MealPlanItem(id=None, meal_plan_id=0, meal_slot=i.meal_slot,
                         food_id=i.food.id if i.food else None, food_name=i.food.name if i.food else "None found")
            for i in plan.items
        ],
    ))

if plan is None:
    empty_state("event_note", "No plan yet",
                f"We'll split your {targets.calorie_target_kcal:,.0f} kcal across five meals and pick foods for each.")
    render_health_disclaimer()
    st.stop()

plan_col, check_col = st.columns([1.6, 1], gap="large")

with plan_col:
    section("Your day", date.today().strftime("%a %d %b"))
    for item in plan.items:
        slot = item.meal_slot.replace("_", " ")
        slot_label = f"{SLOT_TIMES.get(item.meal_slot, '')}  ·  {slot}"
        if item.food:
            food_card(
                item.food.name,
                f"{item.food.calories:.0f} kcal &middot; {item.food.protein_g:.0f} g protein",
                item.reasons,
                slot=slot_label,
            )
        else:
            food_card("Nothing suitable found", "", item.reasons, slot=slot_label)

with check_col:
    section("Check against targets")
    render_source_badge("rule")
    stat("Calories", f"{plan.total_calories:,.0f}", "kcal",
         note=f"{plan.calorie_difference:+,.0f} vs {plan.target_calories:,.0f} target", colour=PAPRIKA)
    st.write("")
    stat("Protein", f"{plan.total_protein_g:.0f}", "g",
         note=f"{plan.protein_difference:+.0f} vs {plan.target_protein_g:.0f} target", colour=LEAF)
    st.caption(
        "Slots get 25 / 10 / 30 / 10 / 25 % of the day's calories. "
        "Treat this as a starting point -- it's only as good as the food database behind it."
    )

render_health_disclaimer()
