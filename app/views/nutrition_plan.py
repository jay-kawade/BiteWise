"""
nutrition_plan.py -- "Targets"

Shows the calculated targets and exactly which formula produced each one.
Nothing on this page is machine-learned.
"""

import plotly.graph_objects as go
import streamlit as st

from app.components.cards import page_header, section, stat
from app.components.disclaimers import render_health_disclaimer
from app.components.session import require_user_id
from app.components.styles import INK, LEAF, MUTED, PAPRIKA, PLUM, SAFFRON, SLATE, render_source_badge
from src.database import repositories as repo
from src.database.models import NutritionTargets
from src.nutrition import formulas
from src.nutrition.calculator import compute_nutrition_targets


def save_targets(user):
    result = compute_nutrition_targets(user)
    repo.save_nutrition_targets(NutritionTargets(
        id=None, user_id=user.id, bmi=result.bmi, bmi_category=result.bmi_category,
        bmr_kcal=result.bmr_kcal, tdee_kcal=result.tdee_kcal, calorie_target_kcal=result.calorie_target_kcal,
        protein_target_g=result.protein_target_g, carb_target_g=result.carb_target_g,
        fat_target_g=result.fat_target_g, fiber_target_g=result.fiber_target_g,
    ))


page_header("Your targets", "Worked out from your profile with standard, published formulas.", eyebrow="You")
user_id = require_user_id()
user = repo.get_user(user_id)

head_l, head_r = st.columns([3, 1], vertical_alignment="center")
with head_l:
    render_source_badge("calculated")
with head_r:
    if st.button("Recalculate", icon=":material/refresh:", width="stretch"):
        save_targets(user)
        st.toast("Targets updated", icon=":material/check:")

targets = repo.get_latest_nutrition_targets(user_id)
if not targets:
    save_targets(user)
    targets = repo.get_latest_nutrition_targets(user_id)

goal = user.goal.replace("_", " ")
activity = user.activity_level.replace("_", " ")

c1, c2, c3 = st.columns(3)
with c1:
    stat("BMI", f"{targets.bmi}", note=targets.bmi_category)
with c2:
    stat("BMR", f"{targets.bmr_kcal:,.0f}", "kcal", note="Energy at complete rest")
with c3:
    stat("TDEE", f"{targets.tdee_kcal:,.0f}", "kcal", note=f"With your activity ({activity})")

section("Daily targets", f"goal: {goal}")

chart_col, tiles_col = st.columns([1, 1.5], gap="large")

with chart_col:
    kcal = {
        "Protein": targets.protein_target_g * 4,
        "Carbs": targets.carb_target_g * 4,
        "Fat": targets.fat_target_g * 9,
    }
    fig = go.Figure(go.Pie(
        labels=list(kcal.keys()), values=list(kcal.values()), hole=0.72, sort=False,
        marker=dict(colors=[LEAF, SAFFRON, PLUM], line=dict(color="#F7F4EE", width=3)),
        textinfo="none", hovertemplate="%{label}: %{percent}<extra></extra>",
    ))
    fig.update_layout(
        height=250, showlegend=True, margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center", font=dict(color=MUTED)),
        annotations=[dict(text=f"<b>{targets.calorie_target_kcal:,.0f}</b><br>kcal / day", showarrow=False,
                          font=dict(size=17, color=INK, family="DM Sans"))],
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

with tiles_col:
    adj = formulas.CALORIE_ADJUSTMENT_BY_GOAL.get(user.goal, 0)
    a, b = st.columns(2)
    with a:
        stat("Calories", f"{targets.calorie_target_kcal:,.0f}", "kcal", note=f"TDEE {adj:+d} kcal for {goal}" if adj else "Same as your TDEE", colour=PAPRIKA)
        st.write("")
        stat("Carbs", f"{targets.carb_target_g:.0f}", "g", note="Whatever's left after protein & fat", colour=SAFFRON)
    with b:
        stat("Protein", f"{targets.protein_target_g:.0f}", "g",
             note=f"{formulas.PROTEIN_G_PER_KG_BY_GOAL.get(user.goal, 1.2)} g per kg body weight", colour=LEAF)
        st.write("")
        stat("Fat", f"{targets.fat_target_g:.0f}", "g",
             note=f"{formulas.FAT_PERCENT_OF_CALORIES:.0%} of calories", colour=PLUM)
    st.write("")
    stat("Fiber", f"{targets.fiber_target_g:.0f}", "g",
         note=f"{formulas.FIBER_G_PER_1000_KCAL:.0f} g per 1000 kcal", colour=SLATE)

st.write("")
with st.expander("How these are calculated", icon=":material/function:"):
    st.markdown(f"""
**BMI** = weight (kg) / height (m)², classified with the WHO adult cut-offs.

**BMR** uses the Mifflin-St Jeor equation (Mifflin et al., *Am J Clin Nutr*, 1990):
- men: `10 × weight + 6.25 × height − 5 × age + 5`
- women: `10 × weight + 6.25 × height − 5 × age − 161`

**TDEE** = BMR × {formulas.ACTIVITY_MULTIPLIERS.get(user.activity_level)} (your activity level, "{activity}").

**Calories** = TDEE {adj:+d} kcal for your goal. A 500 kcal/day gap is roughly 0.45 kg a week -- a rule of thumb, not a law.

**Protein** = {formulas.PROTEIN_G_PER_KG_BY_GOAL.get(user.goal)} g × body weight, inside the range in the ISSN position stand (Jäger et al., 2017).

**Fat** = {formulas.FAT_PERCENT_OF_CALORIES:.0%} of calories, within the 20–35 % AMDR (Institute of Medicine, 2005).

**Carbs** fill the remaining calories. **Fiber** = {formulas.FIBER_G_PER_1000_KCAL:.0f} g per 1000 kcal (IOM adequate intake).

Sources are listed in full in `src/nutrition/formulas.py`.
""")

render_health_disclaimer()
