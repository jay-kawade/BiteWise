"""
cards.py
-------------------------------------------------------------------------------
Small HTML building blocks shared by the pages. Styling for every class used
here lives in styles.py.

Anything that comes from the user or the database (food names, reasons...)
goes through esc() before it is put into HTML.
-------------------------------------------------------------------------------
"""

from html import escape

import streamlit as st

from app.components.styles import BRICK, MACRO_COLOURS


def esc(text) -> str:
    return escape(str(text))


def _html(markup: str):
    # Collapse to one line: indented HTML inside st.markdown is otherwise
    # treated as a markdown code block.
    st.markdown(" ".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def icon(name: str) -> str:
    """Material Symbols glyph for use inside our own HTML (e.g. icon('restaurant'))."""
    return f'<span class="bw-ico">{name}</span>'


def page_header(title: str, subtitle: str = "", eyebrow: str = ""):
    _html(f"""
        <div class="bw-head">
            {f'<div class="bw-eyebrow">{esc(eyebrow)}</div>' if eyebrow else ''}
            <h1 class="bw-title">{esc(title)}</h1>
            {f'<div class="bw-sub">{subtitle}</div>' if subtitle else ''}
        </div>
    """)


def section(title: str, aside: str = ""):
    _html(f'<div class="bw-section"><h4>{esc(title)}</h4><span>{esc(aside)}</span></div>')


def stat(label: str, value: str, unit: str = "", note: str = "", colour: str = ""):
    pip = f'<div class="pip" style="background:{colour}"></div>' if colour else ""
    _html(f"""
        <div class="bw-stat">{pip}
            <div class="lbl">{esc(label)}</div>
            <div class="val">{esc(value)}<small>{esc(unit)}</small></div>
            <div class="note">{esc(note)}</div>
        </div>
    """)


def metric_card(title: str, value: str, subtext: str = ""):
    """Kept for older call sites -- same as stat() without a unit."""
    stat(title, value, note=subtext)


def macro_bar(label: str, consumed: float, target: float, unit: str = "g", key: str = ""):
    colour = MACRO_COLOURS.get(key or label.lower(), MACRO_COLOURS["calories"])
    pct = min(consumed / target, 1.0) * 100 if target > 0 else 0
    over = target > 0 and consumed > target * 1.05
    right = f"{consumed:,.0f} / {target:,.0f} {unit}"
    if over:
        right = f"{consumed - target:,.0f} {unit} over"
    _html(f"""
        <div class="bw-macro">
            <div class="top"><b>{esc(label)}</b><span class="{'over' if over else ''}">{right}</span></div>
            <div class="bw-track"><div class="bw-fill" style="width:{pct:.1f}%;background:{BRICK if over else colour}"></div></div>
        </div>
    """)


def progress_row(label: str, consumed: float, target: float, unit: str = ""):
    """Kept for older call sites."""
    macro_bar(label, consumed, target, unit)


MEAL_ICONS = {
    "breakfast": "egg_alt",
    "lunch": "lunch_dining",
    "dinner": "dinner_dining",
    "snack": "cookie",
    "mid_morning_snack": "nutrition",
    "evening_snack": "coffee",
}


def food_rows(rows):
    """rows: iterable of dicts with name, meta, kcal, (optional) sub, meal."""
    items = []
    for r in rows:
        items.append(f"""
            <div class="bw-row">
                <div class="dot">{icon(MEAL_ICONS.get(r.get('meal', ''), 'restaurant'))}</div>
                <div><div class="name">{esc(r['name'])}</div><div class="meta">{esc(r.get('meta', ''))}</div></div>
                <div class="kcal">{r['kcal']:,.0f} kcal<small>{esc(r.get('sub', ''))}</small></div>
            </div>
        """)
    _html(f'<div class="bw-list">{"".join(items)}</div>')


def facts_panel(rows):
    """rows: (label, value, unit, highlight) tuples, laid out like a nutrition label."""
    cells = "".join(
        f'<div class="{"key" if key else ""}"><span>{esc(label)}</span><b>{esc(value)} {esc(unit)}</b></div>'
        for label, value, unit, key in rows
    )
    _html(f'<div class="bw-facts">{cells}</div>')


def tag(text: str, tone: str = "") -> str:
    return f'<span class="bw-tag {tone}">{esc(text)}</span>'


def food_card(title: str, nums: str, reasons=(), slot: str = "", score: str = ""):
    reasons_html = "".join(f"<li>{esc(r)}</li>" for r in reasons)
    _html(f"""
        <div class="bw-card">
            <div class="hd">
                <div>
                    {f'<div class="slot">{esc(slot)}</div>' if slot else ''}
                    <div class="ttl">{esc(title)}</div>
                    <div class="nums">{nums}</div>
                </div>
                {f'<div class="bw-score">{esc(score)}</div>' if score else ''}
            </div>
            {f'<ul>{reasons_html}</ul>' if reasons_html else ''}
        </div>
    """)


_CHECK_TONES = {"check_circle": ("ok", "check_circle"), "cancel": ("no", "cancel"), "warning": ("warn", "error")}


def checklist(items, verdict: str = ""):
    """
    items: objects with .symbol (":material/check_circle:" etc., see
    food_suitability.py) and .text.
    """
    lis = []
    for item in items:
        name = item.symbol.replace(":material/", "").strip(":")
        tone, glyph = _CHECK_TONES.get(name, ("warn", name))
        lis.append(f'<li><span class="bw-ico {tone}">{glyph}</span><span>{esc(item.text)}</span></li>')
    _html(f'<ul class="bw-check">{"".join(lis)}</ul>')
    if verdict:
        _html(f'<div class="bw-verdict">{esc(verdict)}</div>')


def empty_state(glyph: str, title: str, body: str = ""):
    _html(f"""
        <div class="bw-empty">{icon(glyph)}<b>{esc(title)}</b><p>{body}</p></div>
    """)
