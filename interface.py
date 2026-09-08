"""
Abstraction Layer.

Allows switching implementations without
changing business logic.
"""

from abc import ABC, abstractmethod
from langchain_core.messages import BaseMessage


class ITokenManager(ABC):

    @abstractmethod
    def count_tokens(
        self,
        messages: list[BaseMessage],
    ) -> int:
        """
        Count total tokens.
        """
        pass

    @abstractmethod
    def prepare_messages(
        self,
        messages: list[BaseMessage],
    ) -> list[BaseMessage]:
        """
        Trim messages so they fit
        inside the context window.
        """
        pass