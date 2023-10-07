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


def create_table(table_name: str):
    conn = st.experimental_connection("digitalocean", type="sql")
    with conn.session as s:
        s.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                    uuid VARCHAR(36) PRIMARY KEY,
                    timestamp TIMESTAMPTZ,
                    role VARCHAR(9) CHECK (LENGTH(role) >= 4),
                    content TEXT);"""))
        s.commit()


def save_to_sql(role: str, content: str) -> None:
    conn = st.experimental_connection("digitalocean", type="sql")

    # Get the UUID and timestamp from Streamlit session state and current datetime
    global user_id
    timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    with conn.session as s:
        s.execute(
            text('INSERT INTO ideas (uuid, timestamp, role, content) VALUES (:uuid, :timestamp, :role, :content);'),
            params=dict(uuid=user_id, timestamp=timestamp, role=role, content=content)
        )
        s.commit()


def get_sql_dataframe(table_name: str, uuid: str) -> None:
    conn = st.experimental_connection("digitalocean", type="sql")
    query = f'select * from {table_name} where uuid = :uuid order by timestamp'
    messages = conn.query(query, ttl=timedelta(minutes=1), params={"uuid": uuid})
    st.dataframe(messages)


user_id = init_user_id()
st.write(user_id)

# --- USER INTERACTION ---
user_message = st.chat_input("Send a message")
if user_message:
    st.write(user_message)
