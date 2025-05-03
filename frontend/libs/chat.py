import streamlit as st
from libs.auth import clear_login_token

# -------------------- Dummy backend --------------------
def get_bot_response(user_input):
    mode = st.session_state.get("mode", "Web Search")
    if mode == "Web Search":
        return f"[Web Search Mode] Response to: {user_input}"
    elif mode == "MATLAB Troubleshooting":
        return f"[MATLAB Troubleshooting Mode] Attempting to solve: {user_input}"
    else:
        return "Unknown mode."

# -------------------- Main Chat --------------------
def chat():
    # Session state defaults
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {
            "Welcome Chat": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I assist you today?"}
            ]
        }

    if "current_chat" not in st.session_state:
        st.session_state.current_chat = "Welcome Chat"

    if "mode" not in st.session_state:
        st.session_state.mode = "Web Search"

    if "awaiting_response" not in st.session_state:
        st.session_state.awaiting_response = False

    if "last_input" not in st.session_state:
        st.session_state.last_input = None

    # Sidebar
    with st.sidebar:
        st.title("🧠 Chats")
        chat_names = list(st.session_state.chat_sessions.keys())
        selected_chat = st.radio("Select a chat", chat_names, index=chat_names.index(st.session_state.current_chat))

        if selected_chat != st.session_state.current_chat:
            st.session_state.current_chat = selected_chat
            st.rerun()

        current_chat_empty = len(st.session_state.chat_sessions.get(st.session_state.current_chat, [])) == 0

        if st.button("➕ New Chat"):
            if current_chat_empty:
                st.warning("Please add a message to the current chat before creating a new one.")
            else:
                new_name = f"Chat {len(st.session_state.chat_sessions) + 1}"
                st.session_state.chat_sessions[new_name] = []
                st.session_state.current_chat = new_name
                st.rerun()

        if st.button("🗑️ Delete Chat"):
            if st.session_state.current_chat in st.session_state.chat_sessions:
                del st.session_state.chat_sessions[st.session_state.current_chat]
                remaining = list(st.session_state.chat_sessions.keys())
                if remaining:
                    st.session_state.current_chat = remaining[0]
                else:
                    st.session_state.chat_sessions["New Chat"] = []
                    st.session_state.current_chat = "New Chat"
                st.rerun()

        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            clear_login_token()
            st.rerun()

    # Main area
    chat_history = st.session_state.chat_sessions[st.session_state.current_chat]

    # Display chat
    if chat_history:
        for msg in chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Type your message...")
    else:
        st.markdown("""
        <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 60vh;">
        </div>
        """, unsafe_allow_html=True)
        user_input = st.chat_input("Type your message...")

    if user_input:
        st.session_state.last_input = user_input
        chat_history.append({"role": "user", "content": user_input})
        response = get_bot_response(user_input)
        chat_history.append({"role": "assistant", "content": response})
        st.session_state.awaiting_response = False
        st.rerun()

    # Mode selection buttons
    st.markdown(
        """
        <style>
        .mode-container {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-top: -0.5rem;
            padding-bottom: 1rem;
        }
        .mode-button {
            border: 1px solid #444;
            border-radius: 999px;
            padding: 6px 16px;
            font-size: 14px;
            cursor: pointer;
            background-color: #1f1f1f;
            color: white;
            transition: all 0.2s ease-in-out;
        }
        .mode-button:hover {
            background-color: #333;
        }
        .mode-button.selected {
            background-color: #ff4b4b;
            border-color: #ff4b4b;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="mode-container">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🌐 Web Search", key="web", use_container_width=True, help="Use Web Search mode"):
            st.session_state.mode = "Web Search"
    with col2:
        if st.button("🧮 MATLAB Troubleshooting", key="matlab", use_container_width=True, help="Use MATLAB mode"):
            st.session_state.mode = "MATLAB Troubleshooting"
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"<p style='text-align: center; color: gray;'>Current mode: <strong>{st.session_state.mode}</strong></p>", unsafe_allow_html=True)