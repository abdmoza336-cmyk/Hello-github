import streamlit as st
from denpendancy import get_llm
from memory_service import memory_service

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

#list all active sessions in the sidebar
active_sessions = memory_service.get_all_sessions()
if active_sessions:
    st.sidebar.subheader("Active Sessions")
    for session_id in active_sessions:
        if st.sidebar.button(f"Switch to {session_id}"):
            st.session_state.selected_session = session_id
            st.session_state.history = memory_service._history(session_id)
            st.experimental_rerun()

            
# 2. Button to Start a New Session
# Sidebar button to start a new session
if st.sidebar.button("🆕 Start New Chat"):
    # 1. Generate a new session ID
    st.session_state.session_id = memory_service.create_session_id()
    
    # 2. Clear stored message keys in Streamlit session state
    if "messages" in st.session_state:
        del st.session_state["messages"]
        
    if "history" in st.session_state:
        del st.session_state["history"]
        
    # 3. Refresh Streamlit to render a blank conversation
    st.rerun()