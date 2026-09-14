import re
import uuid
from datetime import datetime, timezone, timedelta
from memory_service import RedisManager

r = RedisManager().redis

SESSION_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{32}$')
USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{8,32}$')
TENANT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{8,32}$')
#VALIDATION FUNCTIONS
def validate_session_id(session_id: str) -> str:
    if not SESSION_ID_PATTERN.fullmatch(session_id):
        raise ValueError("Invalid session ID format. Must be 32 alphanumeric characters.")
    return session_id

def validate_user_id(user_id: str) -> str:
    if not USER_ID_PATTERN.fullmatch(user_id):
        raise ValueError("Invalid user ID format. Must be 8-32 alphanumeric characters.")
    return user_id

def validate_tenant_id(tenant_id: str) -> str:
    if not TENANT_ID_PATTERN.fullmatch(tenant_id):
        raise ValueError("Invalid tenant ID format. Must be 8-32 alphanumeric characters.")
    return tenant_id

#AUTHORIZATION FUNCTION
def authorize_session(session_id: str, user_id: str, tenant_id: str) -> str:
    """Authorize a session based on session ID, user ID, and tenant ID."""
    validate_session_id(session_id)
    validate_user_id(user_id)
    validate_tenant_id(tenant_id)
    
    # Here you would implement the actual authorization logic, e.g., checking against a database
    # For demonstration purposes, we'll just return a success message
    return f"Session {session_id} authorized for user {user_id} in tenant {tenant_id}."
#create session

user_id="Moza12345"
SESSION_TTL_SECONDS=3600
def create_session (user_id:str):
  session_id=str(uuid.uuid4())
  now=datetime.now(timezone.utc)
  expires_at=now+timedelta(seconds=SESSION_TTL_SECONDS)
  # 3. Build session data
  session = {
        "session_id": session_id,
        "user_id": user_id,
        "status": "active",
        "created_at": now.isoformat(),
        "last_activity": now.isoformat(),
        "expires_at": expires_at.isoformat(),}

  # STORE SESSION
  r.hset(f"session:{session_id}", mapping=session)
  r.expire(f"session:{session_id}", SESSION_TTL_SECONDS)
  
  # Associate session with user
  r.sadd(f"user:{user_id}:sessions", session_id)

  return session
# list sessions for a user
def list_sessions(user_id: str):
    validate_user_id(user_id)
    session_ids = r.smembers(f"user:{user_id}:sessions")
    sessions = []
    for session_id in session_ids:
        session_key = f"session:{session_id.decode('utf-8')}"
        if not r.exists(session_key):
            # Remove expired session from user's session set
            r.srem(f"user:{user_id}:sessions", session_id)
            continue
        session_data = r.hgetall(session_key)
        if session_data:
            sessions.append({k.decode('utf-8'): v.decode('utf-8') for k, v in session_data.items()})
    return sessions