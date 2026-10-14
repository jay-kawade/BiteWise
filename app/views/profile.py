"""
profile.py -- "Profile"

Create or edit a profile, including food preferences and restrictions.
Saving recalculates the nutrition targets straight away so every other page
is up to date.
"""

import streamlit as st

from app.components.cards import page_header
from app.components.disclaimers import render_health_disclaimer
from app.components.session import SESSION_KEY
from src.database import repositories as repo
from src.database.models import NutritionTargets, UserProfile
from src.nutrition.calculator import compute_nutrition_targets
from src.nutrition.validation import validate_profile_inputs

SEXES = ["female", "male", "other"]
ACTIVITY = {
    "sedentary": "Sedentary — desk job, little exercise",
    "lightly_active": "Light — exercise 1–3 days a week",
    "moderately_active": "Moderate — exercise 3–5 days a week",
    "very_active": "Very active — hard exercise 6–7 days",
    "extremely_active": "Athlete / physical job",
}
GOALS = {
    "weight_loss": "Lose weight",
    "maintenance": "Maintain",
    "weight_gain": "Gain weight",
    "muscle_gain": "Build muscle",
}
DIETS = {
    "vegan": "Vegan",
    "vegetarian": "Vegetarian",
    "eggetarian": "Eggetarian",
    "non_vegetarian": "Non-vegetarian",
}
CUISINES = ["indian", "continental", "other"]
LEVELS = ["low", "medium", "high"]


def pick(options, current, default):
    keys = list(options)
    return keys.index(current) if current in keys else default


if flash := st.session_state.pop("flash", None):
    st.toast(flash, icon=":material/check:")

current_id = st.session_state.get(SESSION_KEY)
existing = repo.get_user(current_id) if current_id else None
editing = existing is not None

if editing and st.session_state.get("profile_new"):
    existing, editing = None, False

page_header(
    "Your profile" if editing else "Let's set you up",
    "Used to work out your targets and filter suggestions. Change it any time."
    if editing else "A minute of details so BiteWise can size things to you.",
    eyebrow="You",
)

if editing:
    if st.button("Add another profile", icon=":material/person_add:", type="tertiary"):
        st.session_state["profile_new"] = True
        st.rerun()
elif st.session_state.get("profile_new") and repo.list_users():
    if st.button("Back to current profile", icon=":material/arrow_back:", type="tertiary"):
        st.session_state["profile_new"] = False
        st.rerun()


def prefs(kind):
    return ", ".join(repo.get_preference_values(existing.id, kind)) if editing else ""


with st.form("profile_form", border=False):
    with st.container(border=True):
        st.markdown("**About you**")
        c1, c2, c3 = st.columns([2, 1, 1])
        name = c1.text_input("Name", value=existing.name if editing else "")
        age = c2.number_input("Age", min_value=10, max_value=100, value=existing.age if editing else 22)
        sex = c3.selectbox("Sex", SEXES, index=pick(SEXES, existing.sex if editing else None, 0),
                           format_func=str.capitalize)
        c1, c2, c3 = st.columns(3)
        height_cm = c1.number_input("Height (cm)", min_value=100.0, max_value=250.0,
                                    value=float(existing.height_cm) if editing else 165.0, format="%.0f")
        weight_kg = c2.number_input("Weight (kg)", min_value=25.0, max_value=300.0,
                                    value=float(existing.weight_kg) if editing else 60.0, format="%.1f")
        sleep_hours = c3.number_input("Sleep (hours a night)", min_value=0.0, max_value=12.0, step=0.5,
                                      value=float(existing.sleep_hours) if editing else 7.0, format="%.1f")

    with st.container(border=True):
        st.markdown("**Activity & goal**")
        c1, c2 = st.columns(2)
        goal = c1.radio("Goal", list(GOALS), format_func=GOALS.get, horizontal=True,
                        index=pick(GOALS, existing.goal if editing else None, 1))
        activity_level = c2.selectbox("Activity level", list(ACTIVITY), format_func=ACTIVITY.get,
                                      index=pick(ACTIVITY, existing.activity_level if editing else None, 2))
        c1, c2 = st.columns(2)
        exercise_frequency = c1.slider("Workouts per week", 0, 14,
                                       value=existing.exercise_frequency_per_week if editing else 3)
        exercise_type = c2.text_input("What kind? (optional)", placeholder="e.g. gym, running, yoga",
                                      value=existing.exercise_type if editing else "")

    with st.container(border=True):
        st.markdown("**Food**")
        c1, c2, c3 = st.columns(3)
        diet_type = c1.selectbox("Diet", list(DIETS), format_func=DIETS.get,
                                 index=pick(DIETS, existing.diet_type if editing else None, 1))
        cuisine_preference = c2.selectbox("Cuisine", CUISINES, format_func=str.capitalize,
                                          index=pick(CUISINES, existing.cuisine_preference if editing else None, 0))
        meals_per_day = c3.slider("Meals a day", 2, 6, value=existing.meals_per_day if editing else 4)
        c1, c2 = st.columns(2)
        budget_preference = c1.segmented_control(
            "Budget", LEVELS, format_func=str.capitalize,
            default=existing.budget_preference if editing else "medium",
        )
        cooking_time_preference = c2.segmented_control(
            "Time to cook", LEVELS, format_func=str.capitalize,
            default=existing.cooking_time_preference if editing else "medium",
        )

        st.caption("Separate items with commas.")
        c1, c2 = st.columns(2)
        favorite_foods = c1.text_input("Favourites", value=prefs("favorite_food"), placeholder="dosa, rajma")
        disliked_foods = c2.text_input("Dislikes", value=prefs("disliked_food"), placeholder="karela")
        allergies = c1.text_input("Allergies", value=prefs("allergy"), placeholder="peanut, milk")
        avoid_ingredients = c2.text_input("Other things to avoid", value=prefs("avoid_ingredient"),
                                          placeholder="onion, garlic")

    health_notes = st.text_area(
        "Notes for yourself (optional)",
        value=existing.health_notes if editing else "",
        help="Only stored for your reference. BiteWise doesn't read or interpret medical conditions -- "
             "please talk to a healthcare professional about those.",
    )

    submitted = st.form_submit_button("Save profile" if editing else "Create profile", type="primary",
                                      icon=":material/check:")

if submitted:
    errors = validate_profile_inputs(name, int(age), sex, float(height_cm), float(weight_kg),
                                     activity_level, goal, diet_type, float(sleep_hours))
    if errors:
        for e in errors:
            st.error(e, icon=":material/error:")
    else:
        profile = UserProfile(
            id=existing.id if editing else None,
            name=name.strip(), age=int(age), sex=sex, height_cm=float(height_cm), weight_kg=float(weight_kg),
            activity_level=activity_level, exercise_frequency_per_week=int(exercise_frequency),
            exercise_type=exercise_type, sleep_hours=float(sleep_hours), goal=goal, diet_type=diet_type,
            cuisine_preference=cuisine_preference, budget_preference=budget_preference or "medium",
            cooking_time_preference=cooking_time_preference or "medium", meals_per_day=int(meals_per_day),
            health_notes=health_notes,
        )

        if editing:
            repo.update_user(profile)
            user_id = existing.id
        else:
            user_id = repo.create_user(profile)

        repo.set_user_preferences(user_id, "favorite_food", [f.strip() for f in favorite_foods.split(",")])
        repo.set_user_preferences(user_id, "disliked_food", [f.strip() for f in disliked_foods.split(",")])
        repo.set_user_preferences(user_id, "allergy", [f.strip() for f in allergies.split(",")])
        repo.set_user_preferences(user_id, "avoid_ingredient", [f.strip() for f in avoid_ingredients.split(",")])

        # Targets depend on the profile, so refresh them now.
        result = compute_nutrition_targets(repo.get_user(user_id))
        repo.save_nutrition_targets(NutritionTargets(
            id=None, user_id=user_id, bmi=result.bmi, bmi_category=result.bmi_category,
            bmr_kcal=result.bmr_kcal, tdee_kcal=result.tdee_kcal, calorie_target_kcal=result.calorie_target_kcal,
            protein_target_g=result.protein_target_g, carb_target_g=result.carb_target_g,
            fat_target_g=result.fat_target_g, fiber_target_g=result.fiber_target_g,
        ))

        st.session_state[SESSION_KEY] = user_id
        st.session_state["profile_new"] = False
        st.session_state["flash"] = "Profile saved, targets updated"
        st.rerun()

render_health_disclaimer()
