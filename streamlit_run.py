import streamlit as st
from openai import OpenAI
import time
import os

# --------------------------
# Define Accepted Credentials from secrets.toml
# --------------------------
ACCEPTED_CREDENTIALS = st.secrets["credentials"]

# --------------------------
# Login Page Implementation
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Logowanie")
    username = st.text_input("Nazwa użytkownika")
    password = st.text_input("Hasło", type="password")
    if st.button("Zaloguj się"):
        if username in ACCEPTED_CREDENTIALS and ACCEPTED_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.rerun()  # Refresh the app after logging in.
        else:
            st.error("Niepoprawna nazwa użytkownika lub hasło")
    st.stop()  # Prevent the app from running further if not logged in.

# --------------------------
# Main Chat Application
# --------------------------
# Initialize the OpenAI client using the API key from st.secrets.
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# Retrieve the assistant_id from st.secrets
assistant_id = st.secrets["assistant"]["assistant_id"]

# Ensure essential session state variables are set.
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Cześć! Jestem wirtualnym asystentem firmy Bona! W czym mogę Tobie pomóc?"}]
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = assistant_id

# --- API Interaction Functions ---
def create_thread():
    """Creates a new conversation thread via the API."""
    thread = client.beta.threads.create()
    return thread

def add_message(thread_id, role, content):
    """Adds a message (user or assistant) to the given thread."""
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role=role,
        content=content
    )

def run_assistant(thread_id, assistant_id):
    """
    Runs the assistant on the given thread and polls for completion.
    After completion, retrieves all messages in the thread and returns only
    the most recent assistant reply.
    """
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    # Poll until the run is completed.
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
        time.sleep(1)
    # Retrieve all messages in the thread.
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    # Extract only the most recent assistant message.
    assistant_reply = ""
    for message in messages.data:
        if message.role == "assistant":
            for content_item in message.content:
                if content_item.type == "text":
                    assistant_reply = content_item.text.value
                    break
            if assistant_reply:
                break
    return assistant_reply

# --------------------------
# Streamlit Chat Interface (Main App)
# --------------------------
st.title("Porozmawiaj z wirtualnym asystentem Bony!")

if st.button("Wyczyść Sesję"):
    st.session_state.thread_id = None
    st.session_state.messages = [{"role": "assistant", "content": "Cześć! Jestem wirtualnym asystentem firmy Bona! W czym mogę Tobie pomóc?"}]
    st.rerun()

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_input = st.chat_input("Wpisz wiadomość...")
if user_input:
    if st.session_state.thread_id is None:
        thread = create_thread()
        st.session_state.thread_id = thread.id

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    add_message(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input
    )
    
    assistant_reply = run_assistant(
        thread_id=st.session_state.thread_id,
        assistant_id=st.session_state.assistant_id
    )

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    st.chat_message("assistant").write(assistant_reply)

    st.rerun()
