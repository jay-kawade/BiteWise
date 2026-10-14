"""
analytics.py -- "Your week"

Last seven days of logging. Uses src/agent/tools.get_weekly_summary so the
numbers here always match what the assistant says.
"""

from datetime import date, timedelta

import plotly.graph_objects as go
import streamlit as st

from app.components.cards import empty_state, page_header, section, stat
from app.components.disclaimers import render_health_disclaimer
from app.components.session import require_user_id
from app.components.styles import FAINT, LEAF, PAPRIKA, SAND, SLATE
from src.agent.tools import get_weekly_summary
from src.database import repositories as repo
from src.nutrition.calculator import summarize_consumed

page_header("Your week", "The last seven days at a glance.", eyebrow="Plan")
user_id = require_user_id()

summary = get_weekly_summary(user_id)
if summary.get("days_logged", 0) == 0:
    empty_state("bar_chart", "Nothing to show yet",
                "Log a few meals in your food diary and your week will start filling in here.")
    st.page_link("views/food_log.py", label="Open food diary", icon=":material/arrow_forward:")
    render_health_disclaimer()
    st.stop()

end = date.today()
days = [end - timedelta(days=i) for i in range(6, -1, -1)]
entries = repo.get_food_logs_between(user_id, str(days[0]), str(end))
targets = repo.get_latest_nutrition_targets(user_id)

by_date = {}
for e in entries:
    by_date.setdefault(e.log_date, []).append(e)
daily = {d: summarize_consumed(by_date.get(str(d), [])) for d in days}
labels = [d.strftime("%a") if d != end else "Today" for d in days]

avg = summary["average_daily"]
c1, c2, c3, c4 = st.columns(4)
with c1:
    stat("Avg. calories", f"{avg['calories']:,.0f}", "kcal/day", colour=PAPRIKA)
with c2:
    stat("Avg. protein", f"{avg['protein_g']:.0f}", "g/day", colour=LEAF)
with c3:
    stat("Avg. fiber", f"{avg['fiber_g']:.0f}", "g/day", colour=SLATE)
with c4:
    stat("Days logged", f"{summary['days_logged']}", "/ 7", note=f"{summary['total_meals_logged']} items")


def week_chart(key: str, colour: str, target: float | None, unit: str):
    values = [daily[d][key] for d in days]
    bar_colours = [colour if v > 0 else SAND for v in values]
    fig = go.Figure(go.Bar(
        x=labels, y=values, marker=dict(color=bar_colours, cornerradius=6),
        hovertemplate=f"%{{x}}: %{{y:,.0f}} {unit}<extra></extra>",
    ))
    if target:
        fig.add_hline(y=target, line=dict(color=FAINT, width=1.5, dash="dot"),
                      annotation_text=f"target {target:,.0f}", annotation_position="top left",
                      annotation_font=dict(size=11, color=FAINT))
    fig.update_layout(height=260, showlegend=False)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


left, right = st.columns(2, gap="large")
with left:
    section("Calories", "kcal per day")
    week_chart("calories", PAPRIKA, targets.calorie_target_kcal if targets else None, "kcal")
with right:
    section("Protein", "grams per day")
    week_chart("protein_g", LEAF, targets.protein_target_g if targets else None, "g")

section("What stands out")
notes = [
    f"Across {summary['days_logged']} logged day{'s' if summary['days_logged'] != 1 else ''} you averaged "
    f"{avg['calories']:,.0f} kcal, {avg['protein_g']:.0f} g protein, {avg['carbohydrates_g']:.0f} g carbs "
    f"and {avg['fat_g']:.0f} g fat."
]
if summary["days_below_protein_target"] > 0:
    notes.append(f"Protein came in under target on {summary['days_below_protein_target']} "
                 f"of {summary['days_logged']} days.")
if avg["sugar_g"] > 30:
    notes.append(f"Sugar averaged {avg['sugar_g']:.0f} g a day, which is on the high side.")
if avg["sodium_mg"] > 2000:
    notes.append(f"Sodium averaged {avg['sodium_mg']:,.0f} mg a day, which is on the high side.")

for n in notes:
    st.markdown(f"- {n}")
st.caption("Simple observations from your own logs, not a medical reading of them.")

render_health_disclaimer()
