import uuid

import streamlit as st
from denpendancy import get_llm
from memory_service import memory_service
from session_service import create_session, authorize_session,list_sessions

st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="centered")

st.title("🤖 AI Chatbot Assistant")

if "llm" not in st.session_state:
    st.session_state.llm = get_llm()
if "history" not in st.session_state:
    st.session_state.history = memory_service._history("enterprise_session_001")

for message in st.session_state.history.messages:
    if message.type == "human":
        with st.chat_message("user"):
            st.markdown(message.content)
    elif message.type == "ai":
        with st.chat_message("assistant"):
            st.markdown(message.content)

if user_input := st.chat_input("Type your message here..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.history.add_user_message(user_input)

    with st.chat_message("assistant"):
        try:
            stream_response = st.session_state.llm.stream(st.session_state.history.messages)
            full_response = st.write_stream(stream_response)
            st.session_state.history.add_ai_message(full_response)
        except Exception as e:
            st.error(f"Error generating response: {e}")
# Ensure current session is tracked
current_session = st.session_state.get("selected_session", "enterprise_session_001")

# Sidebar button to fetch and display total message count
if st.sidebar.button("📊 Count Messages"):
    count = memory_service.message_count(current_session)
    st.sidebar.info(f"Total messages in session: **{count}**")
# Sidebar button to clear chat history
if st.sidebar.button("🗑️ Clear Chat History") :
    memory_service.clear_session(current_session)

# list sessions for a user
if st.sidebar.button("📋 List Sessions for User")   :
    user_id = st.text_input("Enter User ID to list sessions:")
    if user_id:
        try:
            sessions = list_sessions(user_id)
            if sessions:
                st.sidebar.success(f"Sessions for user {user_id}: {', '.join(sessions)}")
            else:
                st.sidebar.warning(f"No sessions found for user {user_id}.")
        except Exception as e:
            st.sidebar.error(f"Error listing sessions: {e}")




            
# 2. Button to Start a New Session
# Sidebar button to start a new session
if st.sidebar.button("🆕 Start New Chat"):
    # 1. Generate a new session ID
    new_session = create_session("Moza12345")  # Replace with actual user ID
    
    # 2. Update active session keys
    st.session_state["session_id"] = new_session["session_id"]
    st.session_state["selected_session"] = new_session["session_id"]
    
    # 3. Clear the message list for the new chat
    st.session_state["messages"] = []  
    
    # 4. Success message & immediate UI refresh
    st.sidebar.success(f"New session started with ID: {new_session['session_id']}")
    st.rerun()

if st.sidebar.button("Delete Current Session"):
    if "session_id" in st.session_state:
        memory_service.delete_session(st.session_state.session_id)
        del st.session_state["session_id"]
        st.sidebar.success("Current session deleted.")
    else:
        st.warning("No session to delete.")



# Sidebar button setup
if st.sidebar.button("+New Chat"):
    # 1. Reset the message list in Streamlit session state
    st.session_state.messages = []
    
    # 2. Generate a new session ID
    st.session_state.session_id = str(uuid.uuid4())
    
    # 3. Force Streamlit to immediately refresh the UI
    st.rerun()