from langchain_groq import ChatGroq
from langsmith import traceable
from config import settings


llm = ChatGroq(
    model=settings.MODEL_NAME,
    groq_api_key=settings.GROQ_API_KEY,temperature=settings.TEMPERATURE,
    max_tokens=settings.MAX_TOKENS,
    max_retries=settings.MAX_RETRIES)


class LLMFactory:
    """Creates and manages LLM instances."""
    @traceable(name="chat_completion")
    @staticmethod
    def create_chat_model() -> ChatGroq:
        return ChatGroq(
            model=settings.MODEL_NAME,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            max_retries=settings.MAX_RETRIES
        )
    


# Shared singleton instance
llm = LLMFactory.create_chat_model()