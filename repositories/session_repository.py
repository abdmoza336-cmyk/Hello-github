import sys
from pathlib import Path
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

    

