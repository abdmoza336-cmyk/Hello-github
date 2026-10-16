import re
import uuid
from datetime import datetime, timezone, timedelta

from attr.converters import pipe
from memory_service import RedisManager
import memory_service
session_ttl_seconds = 3600  # 1 hour
r = RedisManager().redis

SESSION_ID_PATTERN = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}")
USER_ID_PATTERN = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}")
TENANT_ID_PATTERN = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}")
#VALIDATION FUNCTIONS
def validate_session_id(session_id: str) -> str:
    if not isinstance(session_id, str): # Check if session_id is a string
        raise ValueError("Session ID must be a string.")
    session_id = session_id.strip() # Remove leading/trailing whitespace
    if not session_id: # Check if session_id is empty after stripping
        raise ValueError("Session ID cannot be empty.")
    if not SESSION_ID_PATTERN.fullmatch(session_id):
        raise ValueError("Invalid session ID format. Must be 32 alphanumeric characters.")
    
    return session_id

#def validate_user_id(user_id: str) -> str:
    # 1. Type Check: Ensure the argument is a string before calling string methods
    #if not isinstance(user_id, str):
       # raise ValueError("User ID must be a string.")

    # 2. Sanitize: Clean whitespace so empty spaces aren't considered valid input
    #user_id = user_id.strip()

    # 3. Presence Check: Ensure the string is not empty after trimming
    #if not user_id:
    #    raise ValueError("User ID cannot be empty.")

    # 4. Pattern/Format Check: Validate against business rules or regex patterns
    #if not USER_ID_PATTERN.fullmatch(user_id):
    #    raise ValueError("Invalid user ID format. Must be 8-32 alphanumeric characters.")

    # 5. Return sanitized result
    #return user_id

def validate_tenant_id(tenant_id: str) -> str:
    # 1. Type Check: Ensure the argument is a string before calling string methods
    if not isinstance(tenant_id, str):
        raise ValueError("Tenant ID must be a string.")
    tenant_id = tenant_id.strip()
    if not tenant_id:
        raise ValueError("Tenant ID cannot be empty.")
    if not TENANT_ID_PATTERN.fullmatch(tenant_id):
        raise ValueError("Invalid tenant ID format. Must be 8-32 alphanumeric characters.")
    return tenant_id

# check if a session exists for a given session_id to ensure that we don't create duplicate sessions or perform operations on non-existent sessions.    
async def session_exists(session_id: str) -> bool:
    session_id = validate_session_id(session_id)
    session_key = f"session:{session_id}"
    exists = await r.exists(session_key)
    return exists == 1  # Redis returns 1 if the key exists, 0 otherwise

def create_session (user_id:str, session_metadata:dict[str, str]|None=None,) -> dict[str, str]:
  session_metadata = session_metadata or {} # ensure we dont crash if session_metadata is None
  session_id=str(uuid.uuid4())
  now=datetime.now(timezone.utc)
  expires_at=now+timedelta(seconds=session_ttl_seconds)  
  session_key=f"session:{session_id}" # Create a key for the session for Redis storage
  user_sessions_key=f"user:{user_id}:sessions"
  default_title = session_metadata.get("title", f"Chat ({now.strftime('%b %d, %H:%M')})")


  # 3. Build session data - allow to include extra metadata from the caller (e.g., ip, user_agent)
  session = {
        **session_metadata,  # Extra caller metadata (e.g. ip, user_agent)
        "session_id": session_id,
        "user_id": user_id,
        "title": default_title,
        "status": "active",
        "created_at": now.isoformat(),
        "last_activity": now.isoformat(),
        "expires_at": expires_at.isoformat(),}

  # STORE SESSION IN REDIS Database using pipeline to ensure atomicity and performance
  # Use a Redis pipeline to batch commands for efficiency and atomicity
  with r.pipeline() as pipe:
      
      # Store session data in Redis hash
      pipe.hset(session_key, mapping=session)

      # Set expiration for the session key
      pipe.expire(session_key, session_ttl_seconds)

      # Associate session with user- add the session ID to the user's session set in Redis
      pipe.sadd(user_sessions_key, session_id)
      # Execute the pipeline to perform all operations atomically-all in one round trip to Redis, which is more efficient than executing each command separately.
      pipe.execute()
  return session
def update_session_title(session_id: str, new_title: str) -> None:
    session_id = validate_session_id(session_id)
    session_key = f"session:{session_id}"
    # Check if the session exists before updating
    if not r.exists(session_key):
        raise ValueError("Session does not exist.")
    # Update the title field in the session hash
    r.hset(session_key, "title", new_title) 

def get_session(session_id: str) -> dict[str, str]:
    session_id = validate_session_id(session_id)
    session_key = f"session:{session_id}"
    session_data = r.hgetall(session_key)
    if not session_data:
        raise ValueError("Session does not exist.")
    # Convert bytes to string for all fields in the session data
    return session_data

def get_session_messages(session_id: str) -> list[dict[str, str]]:
    session_id = validate_session_id(session_id)
    session_messages = memory_service.get_messages(session_id)
    return session_messages


# check ownership of a session to ensure that only the user who owns the session can perform operations on it. This is important for security and access control.
async def check_session_ownership(session_id: str, user_id: str) -> bool:
    session_id = validate_session_id(session_id)
    session_key = f"session:{session_id}"

    # fetch the session data from Redis to check if the session exists and if the user_id matches the one stored in the session
    session_data = await r.hgetall(session_key)
    # if the session does not exist, raise an error
    if not session_data:
        raise ValueError("Session does not exist.")
    # check if the user_id in the session data matches the provided user_id
    store_user_id = session_data.get(b"user_id", b"").decode("utf-8")
    if store_user_id != user_id:
        raise ValueError("User does not own this session.")
    return True

# list sessions for a user
def list_sessions(user_id: str):
    user_sessions_key = f"user:{user_id}:sessions"
    session_ids = r.smembers(user_sessions_key)
    sessions = []
    for session_id in session_ids:
        session_key = f"session:{session_id}"
        if not r.exists(session_key):
            # Remove expired session from user's session set
            r.srem(user_sessions_key, session_id)
            continue
        session_data = r.hgetall(session_key)
        if session_data:
            sessions.append({k: v for k, v in session_data.items()})
    return sessions
def delete_session(session_id: str, user_id: str) -> None:
    session_id = validate_session_id(session_id)
    session_key = f"session:{session_id}"
    session_data = r.hgetall(session_key)
    if not session_data:
        raise ValueError("Session does not exist.")
    user_id = session_data.get(b"user_id", b"").decode("utf-8")
    user_sessions_key = f"user:{user_id}:sessions"
    # Use a Redis pipeline to delete the session and remove it from the user's session set atomically
    with r.pipeline() as pipe:
        pipe.delete(session_key)  # Delete the session hash
        pipe.srem(user_sessions_key, session_id)  # Remove the session ID from the user's session set
        pipe.execute()  # Execute the pipeline to perform all operations atomically
