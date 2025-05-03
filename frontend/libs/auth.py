import streamlit as st
import hashlib

# --- Hardcoded credentials ---
VALID_USERNAME = "1"
VALID_PASSWORD = "1"

# --- Utils ---
def hash_creds(username, password):
    return hashlib.sha256(f"{username}:{password}".encode()).hexdigest()

def save_login_token(token):
    st.query_params["token"] = token

def load_login_token():
    return st.query_params.get("token", None)

def clear_login_token():
    st.query_params.clear()

def is_logged_in():
    return st.session_state.get("logged_in", False)

def check_auth():
    if "logged_in" not in st.session_state:
        token = load_login_token()
        expected = hash_creds(VALID_USERNAME, VALID_PASSWORD)
        st.session_state.logged_in = (token == expected)

# --- Login form ---
def login():
    st.title("🔐 Login to AI Troubleshooter")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if username == VALID_USERNAME and password == VALID_PASSWORD:
                st.session_state.logged_in = True
                save_login_token(hash_creds(username, password))
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
