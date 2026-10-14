"""
assistant.py -- "Ask BiteWise"

Chat UI only. All the reasoning and tool calls happen in
src/agent/orchestrator.py.
"""

from pathlib import Path

import streamlit as st

from app.components.cards import page_header
from app.components.disclaimers import render_health_disclaimer
from app.components.session import require_user_id
from src.agent.orchestrator import handle_user_message
from src.utils import config

BOT_AVATAR = str(Path(__file__).resolve().parent.parent / "assets" / "bitewise_mark.svg")

STARTERS = [
    "What should I eat next?",
    "How many calories have I had today?",
    "Make me a meal plan",
    "What can I swap paneer with?",
    "How was my week?",
]

page_header("Ask BiteWise", "Questions about your food, your targets or your log. Answers come from your own data.")
user_id = require_user_id()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

top_l, top_r = st.columns([3, 1], vertical_alignment="center")
with top_l:
    if config.LLM_ASSISTANT_ENABLED:
        st.badge("LLM mode", icon=":material/bolt:", color="green")
    else:
        st.badge("Offline mode · rule-based", icon=":material/rule:", color="gray")
        st.caption("No LLM API key is set, so questions are matched to a fixed set of tools.")
with top_r:
    if st.session_state.chat_history and st.button("Clear chat", icon=":material/delete_sweep:", type="tertiary"):
        st.session_state.chat_history = []
        st.rerun()

pending = None
if not st.session_state.chat_history:
    st.write("")
    st.caption("Try one of these")
    with st.container(horizontal=True):
        for prompt in STARTERS:
            if st.button(prompt):
                pending = prompt

for role, content in st.session_state.chat_history:
    with st.chat_message(role, avatar=":material/person:" if role == "user" else BOT_AVATAR):
        st.markdown(content)

with st.popover("Attach a label photo", icon=":material/attach_file:"):
    uploaded_image = st.file_uploader("Label photo", type=["png", "jpg", "jpeg"], key="assistant_image",
                                      label_visibility="collapsed")
    st.caption("It'll be sent with your next message.")

user_message = st.chat_input("Ask about your food or your day...") or pending

if user_message:
    st.session_state.chat_history.append(("user", user_message))
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(user_message)

    image_bytes = uploaded_image.read() if uploaded_image else None
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Thinking..."):
            response = handle_user_message(user_id, user_message, image_bytes)
        st.markdown(response.text)

    st.session_state.chat_history.append(("assistant", response.text))
    if pending:
        st.rerun()

render_health_disclaimer()
