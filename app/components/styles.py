"""
styles.py
-------------------------------------------------------------------------------
BiteWise look & feel.

The base theme (fonts, widget colours, radius) lives in .streamlit/config.toml.
This file adds the bits Streamlit's theme can't express: our own cards,
macro bars, rings, tags, and some small fixes to Streamlit's defaults.

Colour tokens below are the single source of truth for Python code (charts,
inline SVG). Keep them in sync with config.toml.
-------------------------------------------------------------------------------
"""

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --- colour tokens ----------------------------------------------------------
INK = "#23211C"
MUTED = "#6F6A60"
FAINT = "#A39D91"
PAPER = "#F7F4EE"
SURFACE = "#FFFFFF"
SAND = "#EFEAE0"
LINE = "#E3DCCF"

BASIL = "#2F5D3A"      # brand / primary
BASIL_SOFT = "#E3ECE2"
PAPRIKA = "#D9623B"    # calories
SAFFRON = "#D99A2B"    # carbs
PLUM = "#7A5C99"       # fat
SLATE = "#3F6E8C"      # fiber
LEAF = "#3C7A4E"       # protein
BRICK = "#B8432F"      # warnings / over target

MACRO_COLOURS = {
    "calories": PAPRIKA,
    "protein": LEAF,
    "carbs": SAFFRON,
    "fat": PLUM,
    "fiber": SLATE,
}

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..600,0..1,0&display=block');

/* ---- page frame ---- */
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }}
[data-testid="stDecoration"] {{ display: none; }}
[data-testid="stHeader"] {{ background: transparent; }}
footer {{ visibility: hidden; }}
h1, h2, h3 {{ letter-spacing: -0.015em; }}

/* sidebar nav: slightly tighter, bolder active item */
[data-testid="stSidebarNav"] a span {{ font-size: 0.93rem; }}
[data-testid="stSidebarNav"] a[aria-current="page"] span {{ font-weight: 600; color: {BASIL}; }}
[data-testid="stSidebarNavSeparator"] {{ display: none; }}

/* streamlit's own metric widget, used in a few places */
div[data-testid="stMetric"] {{
    background: {SURFACE}; border: 1px solid {LINE}; border-radius: 12px; padding: .8rem 1rem;
}}
div[data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: .8rem; }}

/* bordered containers read as cards */
div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] {{ gap: .6rem; }}

/* ---- icons inside our own html ---- */
.bw-ico {{
    font-family: 'Material Symbols Rounded'; font-weight: 400; font-style: normal;
    font-size: 1.15em; line-height: 1; vertical-align: -0.2em;
    display: inline-block; font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased;
}}

/* ---- page header ---- */
.bw-head {{ margin: 0 0 1.6rem 0; }}
.bw-eyebrow {{
    font-size: .74rem; font-weight: 600; letter-spacing: .09em; text-transform: uppercase; color: {PAPRIKA};
    margin-bottom: .35rem;
}}
.bw-title {{
    font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 2.15rem; line-height: 1.1;
    color: {INK}; margin: 0; letter-spacing: -0.02em;
}}
.bw-sub {{ color: {MUTED}; font-size: 1rem; margin-top: .45rem; max-width: 60ch; }}

.bw-section {{
    display: flex; align-items: baseline; justify-content: space-between;
    margin: 1.8rem 0 .7rem 0; border-bottom: 1px solid {LINE}; padding-bottom: .4rem;
}}
.bw-section h4 {{
    font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 1.15rem; margin: 0; padding: 0; color: {INK};
}}
.bw-section span {{ color: {FAINT}; font-size: .82rem; }}

/* ---- stat tiles ---- */
.bw-stat {{
    background: {SURFACE}; border: 1px solid {LINE}; border-radius: 12px;
    padding: .9rem 1.05rem .85rem; height: 100%; position: relative;
}}
.bw-stat .lbl {{ font-size: .78rem; color: {MUTED}; font-weight: 500; }}
.bw-stat .val {{
    font-size: 1.65rem; font-weight: 700; color: {INK}; font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em; margin-top: .15rem;
}}
.bw-stat .val small {{ font-size: .85rem; font-weight: 500; color: {MUTED}; margin-left: .2rem; letter-spacing: 0; }}
.bw-stat .note {{ font-size: .8rem; line-height: 1.4; color: {FAINT}; margin-top: .1rem; min-height: 1.4em; }}
.bw-stat .pip {{ position: absolute; top: 1rem; right: 1rem; width: 8px; height: 8px; border-radius: 50%; }}

/* ---- hero card on Today ---- */
.bw-hero {{
    background: {BASIL}; color: {PAPER}; border-radius: 16px; padding: 1.4rem 1.6rem;
    display: flex; gap: 1.6rem; align-items: center; flex-wrap: wrap;
}}
.bw-hero .big {{
    font-family: 'Fraunces', Georgia, serif; font-size: 3rem; font-weight: 600; line-height: 1;
    font-variant-numeric: tabular-nums; color: #fff;
}}
.bw-hero .cap {{ font-size: .85rem; opacity: .8; margin-top: .35rem; color: {PAPER}; }}
.bw-hero .split {{ display: flex; gap: 1.8rem; flex-wrap: wrap; margin-left: auto; }}
.bw-hero .split div b {{ display: block; font-size: 1.25rem; color: #fff; font-variant-numeric: tabular-nums; }}
.bw-hero .split div span {{ font-size: .78rem; opacity: .75; color: {PAPER}; }}

/* ---- macro bars ---- */
.bw-macro {{ margin: .2rem 0 .95rem 0; }}
.bw-macro .top {{ display: flex; justify-content: space-between; font-size: .88rem; margin-bottom: .32rem; }}
.bw-macro .top b {{ font-weight: 600; color: {INK}; }}
.bw-macro .top span {{ color: {MUTED}; font-variant-numeric: tabular-nums; }}
.bw-macro .top span.over {{ color: {BRICK}; font-weight: 600; }}
.bw-track {{ height: 8px; background: {SAND}; border-radius: 99px; overflow: hidden; }}
.bw-fill {{ height: 100%; border-radius: 99px; }}

/* ---- food rows ---- */
.bw-list {{ background: {SURFACE}; border: 1px solid {LINE}; border-radius: 12px; overflow: hidden; }}
.bw-row {{ display: flex; align-items: center; gap: .85rem; padding: .7rem 1rem; border-top: 1px solid {SAND}; }}
.bw-row:first-child {{ border-top: none; }}
.bw-row .dot {{
    width: 34px; height: 34px; border-radius: 9px; background: {SAND}; color: {MUTED};
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}}
.bw-row .name {{ font-weight: 600; color: {INK}; font-size: .95rem; }}
.bw-row .meta {{ color: {MUTED}; font-size: .8rem; }}
.bw-row .kcal {{ margin-left: auto; text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; color: {INK}; white-space: nowrap; }}
.bw-row .kcal small {{ display: block; color: {FAINT}; font-weight: 400; font-size: .75rem; }}

/* ---- nutrition facts panel (scanner) ---- */
.bw-facts {{
    background: {SURFACE}; border: 1px solid {LINE}; border-radius: 12px; padding: .3rem 1.1rem;
    display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); column-gap: 2rem;
}}
.bw-facts div {{
    display: flex; justify-content: space-between; padding: .55rem 0; border-bottom: 1px solid {SAND};
    font-size: .92rem; color: {MUTED};
}}
.bw-facts div b {{ color: {INK}; font-variant-numeric: tabular-nums; }}
.bw-facts div.key {{ color: {INK}; font-weight: 600; }}

/* ---- tags ---- */
.bw-tag {{
    display: inline-flex; align-items: center; gap: .25rem; font-size: .74rem; font-weight: 600;
    padding: .14rem .55rem; border-radius: 99px; background: {SAND}; color: {MUTED}; margin-right: .3rem;
}}
.bw-tag.green {{ background: {BASIL_SOFT}; color: {BASIL}; }}
.bw-tag.orange {{ background: #F8E3D8; color: #A8461F; }}
.bw-tag.plum {{ background: #ECE4F3; color: {PLUM}; }}
.bw-tag.blue {{ background: #E1EBF1; color: {SLATE}; }}

/* ---- recommendation / meal cards ---- */
.bw-card {{
    background: {SURFACE}; border: 1px solid {LINE}; border-radius: 12px; padding: 1rem 1.1rem; margin-bottom: .7rem;
}}
.bw-card .hd {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }}
.bw-card .ttl {{ font-weight: 600; font-size: 1.02rem; color: {INK}; }}
.bw-card .slot {{ font-size: .72rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: {PAPRIKA}; margin-bottom: .15rem; }}
.bw-card .nums {{ color: {MUTED}; font-size: .84rem; margin-top: .25rem; font-variant-numeric: tabular-nums; }}
.bw-card ul {{ margin: .55rem 0 0 0; padding-left: 1.1rem; }}
.bw-card li {{ color: {MUTED}; font-size: .83rem; margin: .1rem 0; }}
.bw-score {{ font-variant-numeric: tabular-nums; font-size: .8rem; color: {BASIL}; font-weight: 600; white-space: nowrap; }}

/* ---- checklist ---- */
.bw-check {{ list-style: none; padding: 0; margin: .3rem 0 .6rem 0; }}
.bw-check li {{ display: flex; gap: .55rem; align-items: flex-start; padding: .32rem 0; font-size: .92rem; color: {INK}; }}
.bw-check li .bw-ico {{ font-size: 1.2rem; vertical-align: 0; }}
.bw-check .ok {{ color: {LEAF}; }}
.bw-check .warn {{ color: {SAFFRON}; }}
.bw-check .no {{ color: {BRICK}; }}
.bw-verdict {{
    border-left: 3px solid {BASIL}; background: {BASIL_SOFT}; padding: .6rem .9rem; border-radius: 0 8px 8px 0;
    font-size: .92rem; color: {INK};
}}

/* ---- empty states ---- */
.bw-empty {{
    border: 1.5px dashed {LINE}; border-radius: 12px; padding: 1.6rem 1.2rem; text-align: center; color: {MUTED};
}}
.bw-empty .bw-ico {{ font-size: 2rem; color: {FAINT}; display: block; margin: 0 auto .4rem; }}
.bw-empty b {{ color: {INK}; display: block; margin-bottom: .2rem; }}
.bw-empty p {{ font-size: .88rem; margin: 0; color: {MUTED}; }}

/* ---- disclaimer footer ---- */
.bw-foot {{
    margin-top: 3rem; padding-top: 1rem; border-top: 1px solid {LINE};
    font-size: .76rem; line-height: 1.5; color: {FAINT}; display: flex; gap: .6rem;
}}
.bw-foot .bw-ico {{ font-size: 1.1rem; color: {FAINT}; }}

/* ---- sidebar profile chip ---- */
.bw-me {{ display: flex; align-items: center; gap: .65rem; padding: .2rem 0 .5rem; }}
.bw-me .av {{
    width: 36px; height: 36px; border-radius: 50%; background: {PAPRIKA}; color: #fff; font-weight: 700;
    display: flex; align-items: center; justify-content: center; font-size: .95rem;
}}
.bw-me b {{ display: block; font-size: .92rem; color: {INK}; }}
.bw-me span {{ font-size: .78rem; color: {MUTED}; }}
</style>
"""


def inject_custom_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --- plotly ------------------------------------------------------------------
# Registered once so every chart in the app shares fonts, colours and the
# quiet gridlines without repeating update_layout() calls on each page.
_template = go.layout.Template()
_template.layout = go.Layout(
    font=dict(family="DM Sans, sans-serif", size=13, color=MUTED),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    colorway=[LEAF, PAPRIKA, SAFFRON, PLUM, SLATE],
    margin=dict(l=8, r=8, t=16, b=8),
    xaxis=dict(showgrid=False, linecolor=LINE, tickcolor=LINE, title=None),
    yaxis=dict(gridcolor=SAND, zeroline=False, title=None),
    hoverlabel=dict(bgcolor=INK, font=dict(color=PAPER, family="DM Sans, sans-serif")),
    bargap=0.45,
)
pio.templates["bitewise"] = _template
pio.templates.default = "bitewise"


# --- source badges -----------------------------------------------------------
# Labels whether a number is a calculated value, an ML prediction, or a
# rule-based recommendation. These three must never be blurred together.
_SOURCE_BADGES = {
    "ml": {"label": "ML prediction", "icon": ":material/model_training:", "color": "violet"},
    "calculated": {"label": "Calculated", "icon": ":material/calculate:", "color": "green"},
    "rule": {"label": "Rule-based", "icon": ":material/rule:", "color": "orange"},
}


def render_source_badge(source: str):
    """source: 'ml', 'calculated', or 'rule'."""
    spec = _SOURCE_BADGES.get(source, _SOURCE_BADGES["calculated"])
    st.badge(spec["label"], icon=spec["icon"], color=spec["color"])
