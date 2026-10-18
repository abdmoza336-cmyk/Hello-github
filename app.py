import uuid
import asyncio
import streamlit as st
from denpendancy import get_llm
from memory_service import memory_service
from session_service import create_session, check_session_ownership,list_sessions,get_session, update_session_title,delete_session
from rate_limiter import RateLimiter

st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="centered")

st.title("🤖 AI Chatbot Assistant")
import auth

# 1. Initialize Authentication State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_name = None

# 2. Sidebar Authentication UI (If not logged in)
if not st.session_state.authenticated:
    st.sidebar.title("🔐 Account Access")
    auth_tab1, auth_tab2 = st.sidebar.tabs(["Login", "Sign Up"])
    
    with auth_tab1:
        st.subheader("Welcome Back")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Log In"):
            user = auth.authenticate_user(login_email, login_password)
            if user:
                st.session_state.authenticated = True
                st.session_state.user_id = user["user_id"]
                st.session_state.user_name = user["name"]
                st.sidebar.success(f"Welcome back, {user['name']}!")
                st.rerun()
            else:
                st.sidebar.error("Invalid email or password.")
                
    with auth_tab2:
        st.subheader("Create Account")
        signup_name = st.text_input("Full Name", key="signup_name")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        
        if st.button("Register"):
            if not signup_name or not signup_email or not signup_password:
                st.sidebar.warning("Please fill out all fields.")
            else:
                success, result = auth.register_user(signup_email, signup_password, signup_name)
                if success:
                    st.sidebar.success("Account created successfully! Please log in.")
                else:
                    st.sidebar.error(result)
                    
    # Stop execution here so unauthenticated users cannot see the app
    st.stop()

# ==========================================
# 3. Main App (Only runs when authenticated!)
# ==========================================
st.sidebar.success(f"Logged in as: {st.session_state.user_name}")

if st.sidebar.button("🚪 Log Out"):
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.rerun()

st.sidebar.markdown("---")

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
# Initialize RateLimiter
rate_limit_exceeded = not RateLimiter.check_rate_limit(st.session_state.user_id)
if rate_limit_exceeded:
    st.warning("You have exceeded the maximum number of requests allowed per hour. Please try again later.")
    st.stop()
if user_input := st.chat_input("Type your message here..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    # ADD USER MESSAGE TO HISTORY.
    st.session_state.history.add_user_message(user_input)
    # Update the session title based on the user's first message if the current title is still the default format
    #OPTION 1:Truncate the title to 50 characters and append "..." if it's longer than 50 characters
    current_session_id = st.session_state.get("session_id")
    if current_session_id:
        session_data=get_session(current_session_id)
        current_session_title=session_data.get("title", "Untitled Chat")
        if current_session_title.startswith("Chat ("):
            new_title = user_input[:50] + "..." if len(user_input) > 50 else user_input
     #OPTION2: ADVANCED :CALL LLM TO GENERATE A SUMMARY TITLE
            #new_title = st.session_state.llm.generate_title(user_input)  # Assuming you have a method to generate a title from the LLM       
            update_session_title(current_session_id, new_title)


    with st.chat_message("assistant"):
        try:
            stream_response = st.session_state.llm.stream(st.session_state.history.messages)
            full_response = st.write_stream(stream_response)
            st.session_state.history.add_ai_message(full_response)
            current_session = st.session_state.get("selected_session", "default_session")


        except Exception as e:
            st.error(f"Error generating response: {e}")

# Sidebar button to fetch and display total message count
if st.sidebar.button("📊 Count Messages"):
    count = memory_service.message_count(current_session)
    st.sidebar.info(f"Total messages in session: **{count}**")
# Sidebar button to clear chat history
if st.sidebar.button("🗑️ Clear Chat History") :
    current_session = st.session_state.get("selected_session", "default_session")
    session_ownership = check_session_ownership(st.session_state.user_id, current_session)
    if not session_ownership:
        st.sidebar.error("You do not have permission to clear this session's history.")
    memory_service.clear_session(current_session)

# list sessions for a user
if st.sidebar.button("📋 Chats"):
    #st.sidebar.subheader("Your Chat Sessions")
    user_sessions = list_sessions(st.session_state.user_id)
    
    if not user_sessions:
        st.sidebar.info("No chat sessions found. Start a new chat!")
    else:
        for session in user_sessions:
            session_title = session.get("title", "Untitled Chat")
            session_id = session.get("session_id")
            
            # Highlight the currently active session
            is_current = session_id == st.session_state.get("session_id")
            button_label = f"📍 {session_title}" if is_current else f"💬 {session_title}"
            
            if st.sidebar.button(button_label, key=f"session_btn_{session_id}"):
                # Switch active session state and rerun app
                st.session_state.session_id = session_id
                # Update the history for the selected session
                st.session_state.history = memory_service._history(session_id)  
                 
                st.rerun()


# 2. Button to Start a New Session
# Sidebar button to start a new session
if st.sidebar.button("🆕 Start New Chat"): 
    new_session = create_session(user_id = st.session_state.user_id, 
                                     session_metadata={"user_name": st.session_state.user_name} )                              
    try:
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
        delete_session(st.session_state.session_id, st.session_state.user_id)
        del st.session_state["session_id"]
        st.sidebar.success("Current session deleted.")
    else:
        st.warning("No session to delete.")



