"""
session.py
-------------------------------------------------------------------------------
Manages "which user is currently active" across the multi-page Streamlit
app. This is a lightweight, session-based active-user selector -- there is
no authentication system in this project (deliberately: no unnecessary auth
systems for a student demo). Multiple profiles can be created (e.g. so a
team can demo different personas), and the sidebar lets you switch between
them.
-------------------------------------------------------------------------------
"""

from html import escape

import streamlit as st

from src.database import repositories as repo

SESSION_KEY = "current_user_id"


def render_user_selector_sidebar():
    users = repo.list_users()

    if not users:
        st.sidebar.caption("No profile yet -- set one up under **Profile** to get started.")
        st.session_state[SESSION_KEY] = None
        return None

    by_id = {u.id: u for u in users}
    current = st.session_state.get(SESSION_KEY)
    if current not in by_id:
        current = users[0].id
        st.session_state[SESSION_KEY] = current

    user = by_id[current]
    goal = user.goal.replace("_", " ")
    st.sidebar.markdown(
        f'<div class="bw-me"><div class="av">{escape(user.name[:1].upper())}</div>'
        f'<div><b>{escape(user.name)}</b><span>{escape(goal.capitalize())} &middot; {escape(user.diet_type.replace("_", "-"))}</span></div></div>',
        unsafe_allow_html=True,
    )

    if len(users) > 1:
        selected = st.sidebar.selectbox(
            "Switch profile",
            options=list(by_id.keys()),
            format_func=lambda uid: by_id[uid].name,
            index=list(by_id.keys()).index(current),
        )
        st.session_state[SESSION_KEY] = selected
        return selected
    return current


def get_current_user_id():
    return st.session_state.get(SESSION_KEY)


def require_user_id():
    """Use at the top of a page that needs an active profile. Stops the page with a friendly message if none exists."""
    user_id = get_current_user_id()
    if user_id is None:
        from app.components.cards import empty_state

        empty_state("person_add", "Set up your profile first",
                    "BiteWise needs your height, weight and goal before it can work anything out.")
        st.page_link("views/profile.py", label="Go to Profile", icon=":material/arrow_forward:")
        st.stop()
    return user_id
