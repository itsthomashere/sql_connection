import os
import streamlit as st
import openai
from sqlalchemy import create_engine, text
import uuid
from datetime import datetime, timedelta

# --- USER INTERACTION ---
user_message = st.chat_input("Send a message")
if user_message:
    st.write(user_message)
