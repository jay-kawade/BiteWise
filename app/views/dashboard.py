"""
dashboard.py -- "Today"

Home screen: calories left for the day, macro progress, what's been eaten
so far, and a few suggestions for the next meal.
"""

from datetime import datetime

import streamlit as st

from app.components.cards import empty_state, food_rows, macro_bar, page_header, section, stat
from app.components.disclaimers import render_health_disclaimer
from app.components.session import get_current_user_id
from app.components.styles import LEAF, PAPRIKA, PLUM, SAFFRON
from src.database import repositories as repo
from src.nutrition.calculator import calculate_remaining_targets, summarize_consumed
from src.recommendation.recommender import recommend_next_foods


def greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


user_id = get_current_user_id()
if user_id is None:
    page_header("Welcome to BiteWise", "Know what's on your plate, and what to put on it next. "
                "Start by telling us a little about yourself.", eyebrow="Hello")
    st.page_link("views/profile.py", label="Create your profile", icon=":material/arrow_forward:")
    st.stop()

user = repo.get_user(user_id)
targets = repo.get_latest_nutrition_targets(user_id)

if targets is None:
    page_header(f"{greeting()}, {user.name.split()[0]}", eyebrow=datetime.now().strftime("%A, %d %B"))
    empty_state("calculate", "No targets yet", "Your daily targets haven't been worked out. It takes one click.")
    st.page_link("views/nutrition_plan.py", label="Calculate my targets", icon=":material/arrow_forward:")
    st.stop()

entries = repo.get_food_logs_for_date(user_id)
consumed = summarize_consumed(entries)
remaining = calculate_remaining_targets(targets, consumed)

page_header(f"{greeting()}, {user.name.split()[0]}", eyebrow=datetime.now().strftime("%A, %d %B"))

# --- hero: calories left ------------------------------------------------------
left = targets.calorie_target_kcal - consumed["calories"]
left_label = "kcal left today" if left >= 0 else "kcal over today's target"
st.markdown(
    f"""<div class="bw-hero">
<div><div class="big">{abs(left):,.0f}</div><div class="cap">{left_label}</div></div>
<div class="split">
<div><b>{targets.calorie_target_kcal:,.0f}</b><span>Daily target</span></div>
<div><b>{consumed['calories']:,.0f}</b><span>Eaten</span></div>
<div><b>{len(entries)}</b><span>Items logged</span></div>
</div></div>""",
    unsafe_allow_html=True,
)

st.write("")
c1, c2, c3, c4 = st.columns(4)
with c1:
    stat("Protein", f"{consumed['protein_g']:.0f}", f"/ {targets.protein_target_g:.0f} g", colour=LEAF)
with c2:
    stat("Carbs", f"{consumed['carbohydrates_g']:.0f}", f"/ {targets.carb_target_g:.0f} g", colour=SAFFRON)
with c3:
    stat("Fat", f"{consumed['fat_g']:.0f}", f"/ {targets.fat_target_g:.0f} g", colour=PLUM)
with c4:
    stat("BMI", f"{targets.bmi}", note=targets.bmi_category, colour=PAPRIKA)

col_left, col_right = st.columns([1.35, 1], gap="large")

with col_left:
    section("Progress", "vs. today's targets")
    macro_bar("Calories", consumed["calories"], targets.calorie_target_kcal, "kcal")
    macro_bar("Protein", consumed["protein_g"], targets.protein_target_g)
    macro_bar("Carbs", consumed["carbohydrates_g"], targets.carb_target_g)
    macro_bar("Fat", consumed["fat_g"], targets.fat_target_g)
    macro_bar("Fiber", consumed["fiber_g"], targets.fiber_target_g)

    section("Eaten today", f"{len(entries)} item{'s' if len(entries) != 1 else ''}")
    if entries:
        food_rows(
            {
                "name": e.food_name,
                "meal": e.meal_type,
                "meta": f"{e.meal_type.capitalize()} · {e.quantity_servings:g} serving{'s' if e.quantity_servings != 1 else ''}",
                "kcal": e.calories,
                "sub": f"{e.protein_g:.0f} g protein",
            }
            for e in reversed(entries)
        )
    else:
        empty_state("restaurant", "Nothing logged yet", "Add your first meal from the food diary or scan a label.")
    st.page_link("views/food_log.py", label="Open food diary", icon=":material/arrow_forward:")

with col_right:
    section("Up next", "fits what's left")
    if remaining["calories"] > 0:
        recs = recommend_next_foods(user_id, remaining["calories"], remaining["protein_g"], user.diet_type, top_n=4)
        if recs:
            food_rows(
                {
                    "name": r.food.name,
                    "meal": r.food.meal_type,
                    "meta": r.food.meal_type.capitalize() if r.food.meal_type else "",
                    "kcal": r.food.calories,
                    "sub": f"{r.food.protein_g:.0f} g protein",
                }
                for r in recs
            )
        else:
            empty_state("search_off", "No match right now", "Nothing in the database fits your remaining budget and restrictions.")
    else:
        empty_state("task_alt", "You've hit today's target", "No more suggestions for today.")
    st.page_link("views/recommendations.py", label="More suggestions", icon=":material/arrow_forward:")
    st.page_link("views/scanner.py", label="Scan a packaged food", icon=":material/document_scanner:")

render_health_disclaimer()
