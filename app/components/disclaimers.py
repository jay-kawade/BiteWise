"""
disclaimers.py
-------------------------------------------------------------------------------
The project brief requires these exact disclaimers to appear in the app.
Centralizing them here guarantees the wording is consistent everywhere and
is never silently altered on one page but not another.

The health disclaimer sits as a quiet footer at the bottom of every page;
the allergen one is shown inline wherever ingredients are checked.
-------------------------------------------------------------------------------
"""

import streamlit as st

HEALTH_DISCLAIMER = (
    "This application provides general nutrition and wellness information "
    "based on user-provided data. Nutritional values and requirements are "
    "estimates and may vary by individual. This system is not intended to "
    "diagnose, treat, or prevent any medical condition and is not a "
    "substitute for advice from a qualified healthcare professional."
)

ALLERGEN_DISCLAIMER = (
    "Ingredient detection is based on available label information and does "
    "not guarantee absence of cross-contamination."
)


def render_health_disclaimer():
    st.markdown(
        f'<div class="bw-foot"><span class="bw-ico">info</span><span>{HEALTH_DISCLAIMER}</span></div>',
        unsafe_allow_html=True,
    )


def render_allergen_disclaimer():
    st.caption(ALLERGEN_DISCLAIMER)
