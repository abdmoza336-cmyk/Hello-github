import sys
from pathlib import Path
from typing import Any
sys.path.append(str(Path(__file__).resolve().parent.parent))    
from memory_service import RedisManager

class SessionRepository:
# handle all redis operations related to sessions 
# redis keys prefix
    SESSION_KEY_PREFIX = "session:"
    USER_SESSION_KEY_PREFIX = "user:"
    USER_SESSION_SUFFIX = ":sessions"
    
    def __init__(self):
        self.redis = RedisManager().redis

    def create_session(self, session_id:str, user_id:str, session_data:dict[str, Any]) -> dict[str, Any]:  
        """
        Create a new session in Redis.
        """
        session_key = self.SESSION_KEY_PREFIX + session_id
        user_session_key = self.USER_SESSION_KEY_PREFIX + str(user_id) + self.USER_SESSION_SUFFIX
        
        

        # Store session data in Redis
        self.redis.hmset(session_key, session_data)
        
        # Add session ID to the user's session set
        self.redis.sadd(user_session_key, session_id)


    

