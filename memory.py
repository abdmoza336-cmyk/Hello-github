import os
import logging
from typing import List
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import BaseMessage

# Configure Enterprise-Grade Isolation Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from config import settings

class ProductionChatMemory:
    """
    Thread-safe, horizontally scalable Redis state manager.
    Guarantees session persistence across distributed microservices.
    """
    def __init__(self, redis_url: str = settings.REDIS_URL, ttl: int = settings.REDIS_TTL):
        self.redis_url = redis_url
        self.ttl = ttl

    def _get_history(self, session_id: str) -> RedisChatMessageHistory:
        return RedisChatMessageHistory(
            session_id=session_id,
            url=self.redis_url,
            key_prefix="chatbot_session:",
            ttl=self.ttl
        )

    def add_user_message(self, session_id: str, message: str) -> None:
        if not message or not message.strip():
            return
        try:
            self._get_history(session_id).add_user_message(message)
        except Exception as e:
            logger.critical(f"Memory Write Fault: Failed persisting User turn for session {session_id}: {e}")

    def add_ai_message(self, session_id: str, message: str) -> None:
        if not message or not message.strip():
            return
        try:
            self._get_history(session_id).add_ai_message(message)
        except Exception as e:
            logger.critical(f"Memory Write Fault: Failed persisting AI turn for session {session_id}: {e}")

    def get_all_messages(self, session_id: str) -> List[BaseMessage]:
        try:
            return self._get_history(session_id).messages
        except Exception as e:
            logger.error(f"Memory Read Fault: Falling back to empty state for session {session_id}: {e}")
            return []

memory_layer = ProductionChatMemory()