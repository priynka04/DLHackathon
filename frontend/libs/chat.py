import streamlit as st
import requests
from uuid import uuid4
from libs.auth import clear_login_token
from datetime import datetime

BACKEND_URL = "http://127.0.0.1:5000/"

# -------------------- Get Response from Backend --------------------
def get_bot_response(user_input):
    user_id = st.session_state.get("user_id")
    chat_id = st.session_state.current_chat_id
    mode = st.session_state.get("mode", "Web Search")

    payload = {
        "user_id": user_id,
        "chat_id": chat_id,
        "question": user_input,
        "mode": mode
    }

    try:
        res = requests.post(f"{BACKEND_URL}/ask", json=payload)
        if res.status_code == 200:
            return res.json().get("answer", "No answer returned.")
        else:
            st.error(f"❌ Failed to get response from backend. Status code: {res.status_code}")
            return "❌ Failed to get response from backend."
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Backend not reachable: {e}")
        return "❌ Backend not reachable."

# -------------------- Image to Query --------------------

def get_query_from_image(image_file):
    try:
        files = {'file': image_file}
        res = requests.post(f"{BACKEND_URL}/image-to-query", files=files)
        if res.status_code == 200:
            return res.json().get("query", "")
        else:
            st.error(f"Image processing failed: {res.status_code}")
            return ""
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with image processing service: {e}")
        return ""




# -------------------- Main Chat --------------------
def chat():
    if "page" not in st.session_state:
        st.session_state.page = "chat"
    user_id = st.session_state.get("user_id")

    # Initialize chat_sessions if not present
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {}

        # Load existing chats for this user
        try:
            res = requests.get(f"{BACKEND_URL}/user/chats/{user_id}")
            if res.status_code == 200:
                chats = res.json().get("chats", [])
                for chat in chats:
                    chat_id = chat["chat_id"]
                    chat_name = chat["chat_name"]
                    st.session_state.chat_sessions[chat_id] = {"chat_name": chat_name, "messages": []}
            else:
                st.error(f"Failed to load chats: {res.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to server to load chats: {e}")
        

    # Initialize current_chat_id if not present or if chat_sessions is empty
    # if "current_chat_id" not in st.session_state:
    #     st.session_state.current_chat_id = next(iter(st.session_state.chat_sessions.keys())) if st.session_state.chat_sessions else None


    # print(st.session_state.current_chat_id)


    if "current_chat_id" not in st.session_state or not st.session_state.chat_sessions:
        if st.session_state.chat_sessions:
            st.session_state.current_chat_id = list(st.session_state.chat_sessions.keys())[0]
            try:
                res = requests.get(f"{BACKEND_URL}/user/chat/{user_id}/{st.session_state.current_chat_id}")
                if res.status_code == 200:
                    st.session_state.chat_sessions[st.session_state.current_chat_id]["messages"] = res.json().get("messages", [])
                else:
                    st.warning("Could not load messages for the required chat.")
            except requests.exceptions.RequestException:
                st.warning("Server unreachable while loading welcome chat messages.")
            st.rerun() # Rerun to display the welcome chat
        else:
            new_id = str(uuid4())
            st.session_state.chat_sessions[new_id] = {"chat_name": "Welcome Chat", "messages": []}
            st.session_state.current_chat_id = new_id
            # Immediately fetch messages for the default chat
            try:
                res = requests.get(f"{BACKEND_URL}/user/chat/{user_id}/{new_id}")
                if res.status_code == 200:
                    st.session_state.chat_sessions[new_id]["messages"] = res.json().get("messages", [])
                else:
                    st.warning("Could not load messages for the welcome chat.")
            except requests.exceptions.RequestException:
                st.warning("Server unreachable while loading welcome chat messages.")
            st.rerun() # Rerun to display the welcome chat


    # print(1)
    # print(st.session_state.chat_sessions)



    if "mode" not in st.session_state:
        st.session_state.mode = "MATLAB Troubleshooting"

    # ---------------- Sidebar ----------------
    with st.sidebar:
        st.title("🧠 Chats")

        chat_names = {chat_id: chat_info["chat_name"] for chat_id, chat_info in st.session_state.chat_sessions.items()}
        current_chat_name = st.session_state.chat_sessions[st.session_state.current_chat_id]["chat_name"]
        selected_chat_name = st.radio("Select a chat", list(chat_names.values()), index=list(chat_names.values()).index(current_chat_name))

        selected_chat_id = [
            chat_id for chat_id, chat_name in chat_names.items()
            if chat_name == selected_chat_name
        ][0]


        if selected_chat_id != st.session_state.current_chat_id:
            st.session_state.current_chat_id = selected_chat_id
            # Fetch messages for the selected chat
            try:
                res = requests.get(f"{BACKEND_URL}/user/chat/{user_id}/{selected_chat_id}")
                if res.status_code == 200:
                    st.session_state.chat_sessions[selected_chat_id]["messages"] = res.json().get("messages", [])
                else:
                    st.warning(f"Could not load messages for chat ID: {selected_chat_id}")
            except requests.exceptions.RequestException:
                st.warning("Server unreachable while loading chat messages.")
            st.rerun()

        # print("------------------")
        # print(st.session_state.chat_sessions)

        if st.button("➕ New Chat"):
            try:
                chat_name = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                res = requests.post(f"{BACKEND_URL}/create-chat", json={
                    "user_id": user_id,
                    "chat_name": chat_name
                })
                if res.status_code == 200:
                    chat_data = res.json()
                    new_id = chat_data["chat_id"]
                    st.session_state.chat_sessions[new_id] = {
                        "chat_name": chat_data["chat_name"],
                        "messages": []
                    }
                    st.session_state.current_chat_id = new_id
                    st.rerun()
                else:
                    st.error("Failed to create new chat.")
            except requests.exceptions.RequestException:
                st.error("Could not reach server to create new chat.")

        if st.button("📊 Image Troubleshooting"):
            st.session_state.page = "image_upload"
            st.rerun()


        if st.button("🗑️ Delete Chat"):
            chat_id = st.session_state.current_chat_id
            try:
                res = requests.post(f"{BACKEND_URL}/delete-chat", json={
                    "user_id": user_id,
                    "chat_id": chat_id
                })
                if res.status_code == 200:
                    del st.session_state.chat_sessions[chat_id]
                    if st.session_state.chat_sessions:
                        st.session_state.current_chat_id = list(st.session_state.chat_sessions.keys())[0]
                        st.rerun() # Rerun to update the selected chat
                    else:
                        # Create default if no chats left
                        new_id = str(uuid4())
                        st.session_state.chat_sessions[new_id] = {"chat_name": "Welcome Chat", "messages": []}
                        st.session_state.current_chat_id = new_id
                        st.rerun()
                else:
                    st.error("Failed to delete chat.")
            except requests.exceptions.RequestException:
                st.error("Server unreachable while deleting chat.")

        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            clear_login_token()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    if st.session_state.page == "image_upload":
        st.title("🧮 MATLAB Image Troubleshooting")

        uploaded_file = st.file_uploader("Upload an image of the MATLAB error or code", type=["png", "jpg", "jpeg"])

        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded image", use_column_width=True)

            if st.button("Generate Answer from Image"):
                query = get_query_from_image(uploaded_file)
                if query:
                    with st.expander("🔍 Extracted Query", expanded=True):
                        st.code(query)

                    response = get_bot_response(query)

                    st.subheader("🧠 Assistant's Answer")
                    st.markdown(response)

        st.button("🔙 Back to Chat", on_click=lambda: st.session_state.update({"page": "chat"}))
        st.stop()  # ⛔ Prevents the chat UI from rendering below



    # ---------------- Main Chat Display ----------------
    current_chat_id = st.session_state.current_chat_id
    chat_info = st.session_state.chat_sessions[current_chat_id]
    chat_history = chat_info.get("messages", [])


    # for msg in chat_history:
    #     print("-------------------")
    #     print(msg)
    #     print("--------------------")
    #     if "question" in msg and "answer" in msg:
    #         with st.chat_message(msg["question"]):
    #             st.markdown(msg["answer"])

    for msg in chat_history:
        if "question" in msg and "answer" in msg:
            # User message
            with st.chat_message("user"):
                st.markdown(f"**You:** {msg['question']}")
            
            # Assistant/AI message
            with st.chat_message("assistant"):
                st.markdown(msg["answer"])


    user_input = st.chat_input("Type your message...")



    # if user_input:
    #     st.session_state.chat_sessions[current_chat_id]["messages"].append({"role": "user", "content": user_input})
    #     response = get_bot_response(user_input)
    #     st.session_state.chat_sessions[current_chat_id]["messages"].append({"role": "assistant", "content": response})
    #     st.rerun()

    if user_input:
        # Append user message
        st.session_state.chat_sessions[current_chat_id]["messages"].append({
            "question": user_input
        })

        with st.chat_message("user"):
            st.markdown(f"**You:** {user_input}")

        # Get and display bot response immediately
        response = get_bot_response(user_input)

        st.session_state.chat_sessions[current_chat_id]["messages"][-1]["answer"] = response

        with st.chat_message("assistant"):
            st.markdown(response)

        # Optionally rerun if needed for other updates
        # st.rerun()


    # ---------------- Mode Selector ----------------
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