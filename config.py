from pydantic_settings import BaseSettings, SettingsConfigDict
class settings (BaseSettings):
    MODEL_NAME: str
    GROQ_API_KEY: str
    LANGCHAIN_API_KEY: str
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 400
    MAX_RETRIES: int = 3
     
     # 2. Context window management settings.
     # Maximum context window supported by the model
    MAX_CONTEXT_TOKENS: int = 128000

    # Tokens reserved for the model's response
    RESERVED_OUTPUT_TOKENS: int = 4000
    

    # Always keep the System Prompt
    INCLUDE_SYSTEM: bool = True

    # Do not split messages in half
    ALLOW_PARTIAL: bool = False

    #Redis configuration
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str
    REDIS_URL: str

    REDIS_PREFIX : str = "enterprise:chat:"

    REDIS_TTL : int = 60 * 60 * 24 * 30 # 30 days message retention
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_CHAT_TTL: int = 86400




    model_config = SettingsConfigDict(env_file=".env" ,case_sensitive=False ,extra="ignore" )
settings=settings()
