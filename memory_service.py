"""
memory_service.py

Enterprise-grade Redis Memory Service (Part 1)

Features
--------
✓ Redis Connection Pool
✓ Singleton Redis Client
✓ Structured Logging
✓ Session Validation
✓ Retry Support
✓ Health Checks
✓ Configuration Driven
"""

from __future__ import annotations
import logging
import re
from threading import Lock
import uuid
from portalocker import redis
from redis import Redis, ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError, RedisError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
#from langchain_redis import RedisChatMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from config import settings

logger = logging.getLogger(__name__)
SESSION_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")

# Production retry logic for transient network issues
redis_retry = retry(
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)

def validate_session_id(session_id: str) -> str:
    """Validates session ID format to prevent injection or key pollution."""
    if not session_id or not SESSION_PATTERN.fullmatch(session_id):
        raise ValueError(f"Invalid session ID: {session_id}")
    return session_id

class RedisManager:
    """Thread-safe Singleton managing a shared Redis connection pool."""
    _instance, _lock = None, Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    pool = ConnectionPool.from_url(
                        settings.REDIS_URL,
                        max_connections=settings.REDIS_MAX_CONNECTIONS,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True,
                        decode_responses=True,
                    )
                    cls._instance.redis = Redis(connection_pool=pool)
                    logger.info("Redis connection pool initialized.")
        return cls._instance

class RedisHealth:
    """Health monitor for Redis connectivity."""
    def __init__(self):
        self.client = RedisManager().redis

    @redis_retry
    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except RedisError:
            logger.exception("Redis health check failed.")
            return False

# ==========================================================
# Memory Service
# ==========================================================

class MemoryService:
    """
    Enterprise Redis-backed conversation memory.

    Responsibilities
    ----------------
    - Create or retrieve chat history
    - Add user messages
    - Add AI messages
    - Read conversation history
    - Clear conversations
    - Delete sessions
    - Manage conversation TTL
    """

    def __init__(self):

        self.redis = RedisManager().redis

        self.default_ttl = settings.REDIS_CHAT_TTL

    # ------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------
    @staticmethod
    def create_session_id() -> str:
        """Generates a unique session ID."""
        return str(uuid.uuid4())

    def _history(
        self,
        session_id: str,
    ) -> RedisChatMessageHistory:

        session_id = validate_session_id(session_id)

        return RedisChatMessageHistory(
            session_id=session_id,
            url=settings.REDIS_URL,
            ttl=self.default_ttl,
        )

    # ------------------------------------------------------
    # Public API
    # ------------------------------------------------------

    @redis_retry
    def get_history(
        self,
        session_id: str,
    ) -> RedisChatMessageHistory:

        try:

            history = self._history(session_id)

            logger.info(
                "Loaded history for session=%s",
                session_id,
            )

            return history

        except Exception:

            logger.exception(
                "Failed loading history."
            )

            raise

    # ------------------------------------------------------

    @redis_retry
    def get_messages(
        self,
        session_id: str,
    ):

        history = self._history(session_id)

        return history.messages

    # ------------------------------------------------------

    @redis_retry
    def add_user_message(
        self,
        session_id: str,
        message: str,
    ):

        history = self._history(session_id)

        history.add_user_message(message)

        logger.info(
            "User message stored."
        )

    # ------------------------------------------------------

    @redis_retry
    def add_ai_message(
        self,
        session_id: str,
        message: str,
    ):

        history = self._history(session_id)

        history.add_ai_message(message)

        logger.info(
            "Assistant message stored."
        )

    # ------------------------------------------------------

    @redis_retry
    def add_messages(
        self,
        session_id: str,
        user_message: str,
        ai_message: str,
    ):

        history = self._history(session_id)

        history.add_user_message(user_message)

        history.add_ai_message(ai_message)

        logger.info(
            "Conversation stored."
        )

    # ------------------------------------------------------

    @redis_retry
    def message_count(
        self,
        session_id: str,
    ) -> int:

        history = self._history(session_id)

        return len(history.messages)

    # ------------------------------------------------------

    @redis_retry
    def session_exists(
        self,
        session_id: str,
    ) -> bool:

        key = f"chat:{validate_session_id(session_id)}"

        return self.redis.exists(key) == 1

    # ------------------------------------------------------

    @redis_retry
    def clear_session(
        self,
        session_id: str,
    ):

        history = self._history(session_id)

        history.clear()

        logger.info(
            "Conversation cleared."
        )

    # ------------------------------------------------------

    @redis_retry
    def delete_session(
        self,
        session_id: str,
    ):

        key = f"chat:{validate_session_id(session_id)}"

        self.redis.delete(key)

        logger.info(
            "Conversation deleted."
        )

    # ------------------------------------------------------

    @redis_retry
    def refresh_ttl(
        self,
        session_id: str,
    ):

        key = f"chat:{validate_session_id(session_id)}"

        self.redis.expire(
            key,
            self.default_ttl,
        )
    
     # ------------------------------------------------------

    @redis_retry
    def get_all_sessions(self) -> list[str]:
        """Returns a list of all active session IDs."""
        redis = RedisManager().redis
        keys = redis.keys("chat:*")
        # Handle string or bytes decoding cleanly
        return [
            k.decode().split(":", 1)[1] if isinstance(k, bytes) else k.split(":", 1)[1] 
            for k in keys
        ]


    # ------------------------------------------------------

    @redis_retry
    def get_ttl(
        self,
        session_id: str,
    ) -> int:

        key = f"chat:{validate_session_id(session_id)}"

        return self.redis.ttl(key)

    # ------------------------------------------------------

    @redis_retry
    def export_history(
        self,
        session_id: str,
    ):

        history = self._history(session_id)

        return [
            {
                "type": m.type,
                "content": m.content,
            }
            for m in history.messages
        ]
    
 

# Singleton Memory Service

memory_service = MemoryService()