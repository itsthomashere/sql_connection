import os
import streamlit as st
import openai
import constants as c
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import uuid
from datetime import datetime, timedelta


def hide_st_style() -> None:
    hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
    st.markdown(hide_st_style, unsafe_allow_html=True)


@st.cache_data
def init_user_id() -> str:
    """Initialize or retrieve the user ID stored in session_state."""
    # If "user_id" is not already in session_state, generate a new UUID and store it.
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = str(uuid.uuid4())

    # Return the current or newly generated user ID.
    return st.session_state["user_id"]


def create_chat_completion(model: str, messages: list[dict[str, str]]) -> None:
    """Generate and display chat completion using OpenAI and Streamlit."""
    with st.chat_message(name="assistant", avatar=c.ASSISTANT_ICON):
        message_placeholder = st.empty()
        full_response = ""
        for response in openai.ChatCompletion.create(
            model=model,
            messages=messages,
            stream=True,
        ):
            full_response += response.choices[0].delta.get("content", "")
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    return full_response

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

# --- CONFIGURE API KEY
openai.api_key = os.environ.get("OPENAI_API_KEY")

hide_st_style()
create_table("ideas")

user_id = init_user_id()
st.write(user_id)

# --- INIT SESSION_STATE MESSAGES---
if "messages" not in st.session_state.keys():
    st.session_state["messages"] = [{"role": "system", "content": c.SYSTEM_PROMPT}]

# --- SETUP TEMPORARY TITLE & DESCRIPTION ---
if len(st.session_state["messages"]) == 1:
    st.title("How to leverage AI for social good.")
    st.markdown(c.ABOUT_SEGMENT)

# --- DISPLAY CONVERSATION HISTORY EVERY TIME THERE'S A NEW INTERACTION FROM THE USER ---
for message in st.session_state["messages"]:
    if message["role"] != "system":
        with st.chat_message(name=message["role"], avatar=(
            c.ASSISTANT_ICON if message["role"] == "assistant" else c.USER_ICON
        )):
            st.write(message["content"])

# --- USER INTERACTION ---
user_message = st.chat_input("Send a message")
if user_message:
    # --- SAVE MESSAGE TO SQL DATABASE
    save_to_sql(role="user", content=user_message)
#    with conn.session as s:
#        s.execute(text(f'CREATE TABLE IF NOT EXISTS ideas (role TEXT, content TEXT);'))
#        s.execute(
#            text('INSERT INTO ideas (role, content) VALUES (:role, :content);'),
#            params=dict(role="user", content=user_message))


    # --- APPEND USER MESSAGE TO SESSION_STATE ---
    st.session_state["messages"].append({"role": "user", "content": user_message})


    # --- DISPLAY USER MESSAGE ---
    with st.chat_message(name="user", avatar=c.USER_ICON):
        st.write(user_message)
    
    response = create_chat_completion(model="gpt-4", messages=st.session_state["messages"])

    save_to_sql(role="assistant", content=response)

    # --- APPEND USER MESSAGE TO SESSION_STATE ---
    st.session_state["messages"].append({"role": "assistant", "content": response})

#st.write(st.session_state)
#st.write(st.session_state["uuid"])

get_sql_dataframe("ideas", user_id)
