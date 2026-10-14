"""
scanner.py -- "Scan a label"

Upload a photo of a nutrition label -> OCR -> parsed values, ingredients,
allergen check, and a personal suitability read-out. Every step shows how
confident it is, and the ML meal-type guess is labelled separately.
"""

import streamlit as st

from app.components.cards import checklist, esc, facts_panel, page_header, section, tag
from app.components.disclaimers import render_allergen_disclaimer, render_health_disclaimer
from app.components.session import require_user_id
from app.components.styles import render_source_badge
from src.database import repositories as repo
from src.database.models import FoodLogEntry
from src.ml.predict import is_model_available, predict_meal_type
from src.nutrition.calculator import calculate_remaining_targets, summarize_consumed
from src.scanner.ocr import is_real_ocr_available
from src.scanner.scanner_service import scan_food_label

NUTRIENT_LABELS = {
    "calories": ("Energy", "kcal"),
    "protein_g": ("Protein", "g"),
    "carbohydrates_g": ("Carbs", "g"),
    "fat_g": ("Fat", "g"),
    "saturated_fat_g": ("Sat. fat", "g"),
    "sugar_g": ("Sugar", "g"),
    "fiber_g": ("Fiber", "g"),
    "sodium_mg": ("Sodium", "mg"),
    "serving_size_g": ("Serving", "g"),
}

page_header("Scan a label", "Snap the nutrition panel on any packaged food and we'll read it for you.", eyebrow="Track")
user_id = require_user_id()

real_ocr = is_real_ocr_available()

upload_col, info_col = st.columns([1.4, 1], gap="large")
with upload_col:
    uploaded_file = st.file_uploader("Label photo", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    use_sample = st.toggle("Use a sample label instead", value=uploaded_file is None,
                           help="Handy for a demo when you don't have a packet nearby.")
    scan_clicked = st.button("Scan label", type="primary", icon=":material/document_scanner:")

with info_col:
    with st.container(border=True):
        st.markdown("**For a clean read**")
        st.markdown(
            "- Shoot straight on, not at an angle\n"
            "- Fill the frame with the nutrition table\n"
            "- Avoid glare from shiny wrappers"
        )
        if real_ocr:
            st.caption(":material/check_circle: Tesseract OCR is installed.")
        else:
            st.caption(":material/science: Tesseract isn't installed, so scans run in **mock mode** "
                       "using a built-in sample label. See the README to enable real OCR.")

if scan_clicked:
    if not uploaded_file and not use_sample:
        st.error("Upload a photo, or switch on the sample label.", icon=":material/error:")
    else:
        targets = repo.get_latest_nutrition_targets(user_id)
        remaining = None
        if targets:
            remaining = calculate_remaining_targets(targets, summarize_consumed(repo.get_food_logs_for_date(user_id)))

        with st.spinner("Reading label..."):
            st.session_state["last_scan_result"] = scan_food_label(
                image_bytes=uploaded_file.read() if uploaded_file else b"",
                user_id=user_id,
                remaining_calorie_budget=remaining["calories"] if remaining else None,
                remaining_protein_budget=remaining["protein_g"] if remaining else None,
            )

result = st.session_state.get("last_scan_result")
if result:
    mode = tag("Real OCR", "green") if result.ocr_mode == "real" else tag("Mock OCR · demo", "orange")
    st.markdown(
        f'<div style="margin-top:1.6rem">{mode}{tag(f"OCR {result.ocr_confidence:.0%}")}'
        f'{tag(f"Parsing {result.parsing_confidence:.0%}", "blue")}</div>',
        unsafe_allow_html=True,
    )

    section("Nutrition facts", "as read from the label")
    if result.parsed_nutrition:
        rows = []
        for key, value in result.parsed_nutrition.items():
            label, unit = NUTRIENT_LABELS.get(key, (key.replace("_", " ").capitalize(), ""))
            shown = f"{value:g}" if isinstance(value, (int, float)) else str(value)
            rows.append((label, shown, unit, key in ("calories", "protein_g")))
        facts_panel(rows)
    else:
        st.warning("Couldn't pick out any nutrition values. Try a sharper photo.", icon=":material/warning:")

    if result.parsing_confidence < 0.5:
        st.warning("Low confidence on this one -- double-check the numbers before logging.", icon=":material/warning:")
    if result.parsing_warnings:
        with st.expander(f"Parsing notes ({len(result.parsing_warnings)})"):
            for w in result.parsing_warnings:
                st.markdown(f"- {w}")
    with st.expander("Raw OCR text"):
        st.code(result.raw_ocr_text, language=None)

    left, right = st.columns(2, gap="large")
    with left:
        section("Ingredients")
        if result.ingredients:
            st.markdown("".join(tag(i) for i in result.ingredients), unsafe_allow_html=True)
        else:
            st.caption("No ingredient list found in the text.")

        section("Allergens")
        if result.allergen_warnings:
            found = "\n".join(f"- {w.replace('_', ' ')}" for w in result.allergen_warnings)
            st.error(f"**Found on your avoid list**\n\n{found}", icon=":material/warning:")
        elif result.ingredients:
            st.success("Nothing from your allergy or avoid list was found.", icon=":material/check_circle:")
        if result.ingredients or result.allergen_warnings:
            render_allergen_disclaimer()

    with right:
        if result.suitability:
            section("For you")
            checklist(result.suitability.checklist, verdict=result.suitability.suitability_label)

        if result.parsed_nutrition and is_model_available():
            prediction = predict_meal_type(
                result.parsed_nutrition, serving_size_g=result.parsed_nutrition.get("serving_size_g", 100.0)
            )
            if prediction:
                section("Likely meal")
                render_source_badge("ml")
                st.markdown(
                    f"Looks most like a **{esc(prediction.predicted_meal_type)}** item "
                    f"({prediction.confidence:.0%} confidence, {esc(prediction.model_name.replace("_", " "))})."
                )

    section("Log it")
    with st.form("log_scanned_food", border=False):
        c1, c2, c3 = st.columns([2, 1, 1])
        food_name = c1.text_input("Name", value="Scanned item")
        meal_type = c2.selectbox("Meal", ["breakfast", "lunch", "dinner", "snack"], format_func=str.capitalize)
        quantity = c3.number_input("Servings", min_value=0.1, max_value=20.0, value=1.0, step=0.5, format="%.1f")
        log_it = st.form_submit_button("Add to diary", icon=":material/add:")

    if log_it:
        if not result.parsed_nutrition:
            st.error("There are no parsed values to log.", icon=":material/error:")
        else:
            n = result.parsed_nutrition
            repo.log_food(FoodLogEntry(
                id=None, user_id=user_id, food_id=None, food_name=food_name, meal_type=meal_type,
                quantity_servings=quantity,
                calories=n.get("calories", 0.0) * quantity,
                protein_g=n.get("protein_g", 0.0) * quantity,
                carbohydrates_g=n.get("carbohydrates_g", 0.0) * quantity,
                fat_g=n.get("fat_g", 0.0) * quantity,
                fiber_g=n.get("fiber_g", 0.0) * quantity,
                sugar_g=n.get("sugar_g", 0.0) * quantity,
                sodium_mg=n.get("sodium_mg", 0.0) * quantity,
                log_source="scanned",
            ))
            st.toast(f"Added {food_name} to {meal_type}", icon=":material/check:")

render_health_disclaimer()
