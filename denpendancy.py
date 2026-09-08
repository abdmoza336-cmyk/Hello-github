"""
Dependency Injection.

Creates reusable objects.
"""

from llm import llm
from memory import memory_layer


def get_llm():
    return llm

def get_memory_layer():
    return memory_layer
#Or, if you don't want a shared instance
from llm import LLMFactory


def get_llm():
    return LLMFactory.create_chat_model()
