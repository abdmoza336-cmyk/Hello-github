import uuid
import asyncio
import streamlit as st
from denpendancy import get_llm
from memory_service import memory_service
from session_service import create_session, check_session_ownership,list_sessions

st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="centered")

st.title("🤖 AI Chatbot Assistant")

if "llm" not in st.session_state:
    st.session_state.llm = get_llm()
if "history" not in st.session_state:
    session_id=str(uuid.uuid4())
    st.session_state.history = memory_service._history(session_id)

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
current_session = st.session_state.get("selected_session", "default_session")

# Sidebar button to fetch and display total message count
if st.sidebar.button("📊 Count Messages"):
    count = memory_service.message_count(current_session)
    st.sidebar.info(f"Total messages in session: **{count}**")
# Sidebar button to clear chat history
if st.sidebar.button("🗑️ Clear Chat History") :
    memory_service.clear_session(current_session)

# list sessions for a user
if st.sidebar.button("📋 List Sessions for User"):
    user_id = st.session_state.get("user_id", "default_user")  # Use existing user_id or generate a new one
    sessions = list_sessions(user_id=user_id)
    if sessions:
        st.sidebar.write(sessions)
    else:
        st.sidebar.info("No sessions found for this user.")

# 2. Button to Start a New Session
# Sidebar button to start a new session
if st.sidebar.button("🆕 Start New Chat"):                               
    #user_id = str(uuid.uuid4())  
    
    try:
        new_session = create_session(user_id=user_id)
        
        # Let's check what's actually returned
        if not new_session:
            st.error("create_session returned None! Check Redis connection.")
            st.stop()
            
        new_session_id = new_session["session_id"]
        st.session_state.session_id = new_session_id  
        st.session_state.selected_session = new_session_id
        st.session_state.history = memory_service._history(new_session_id)                                      
        st.rerun()
        
    except Exception as e:
        st.error(f"Error creating session: {e}")

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