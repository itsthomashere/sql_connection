import os
import streamlit as st
import openai
from sqlalchemy import create_engine, text
import uuid
from datetime import datetime, timedelta

@st.cache_data
def init_user_id() -> str:
    """Initialize or retrieve the user ID stored in session_state."""
    # If "user_id" is not already in session_state, generate a new UUID and store it.
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = str(uuid.uuid4())

    # Return the current or newly generated user ID.
    return st.session_state["user_id"]

user_id = init_user_id()
st.write(user_id)

# --- USER INTERACTION ---
user_message = st.chat_input("Send a message")
if user_message:
    st.write(user_message)
