import logging
from pydantic_settings import BaseSettings
from pydantic import model_validator

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Server Config
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # App Metadata
    APP_NAME: str = "VinBank Agent"
    APP_VERSION: str = "1.0.0"

    # Security & Networking
    AGENT_API_KEY: str = "secret"
    ALLOWED_ORIGINS: str = "*"
    
    # Economics & Limits
    RATE_LIMIT_PER_MINUTE: int = 10
    MONTHLY_BUDGET_USD: float = 10.0

    # Infrastructure
    REDIS_URL: str = "redis://redis:6379"
    LOG_LEVEL: str = "INFO"

    # LLM Integrations
    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    
    class Config:
        env_file = ".env"

    @model_validator(mode='after')
    def validate_production(self):
        """12-Factor style validation to ensure security holds in production"""
        if self.ENVIRONMENT.lower() == "production":
            if self.AGENT_API_KEY in ["secret", "dev-key-change-me", ""]:
                raise ValueError("CRITICAL: AGENT_API_KEY must be securely overwritten in production!")
        
        if not self.OPENAI_API_KEY and not self.GEMINI_API_KEY:
            logger.warning("No Real LLM Keys (OpenAI/Gemini) detected — Application will fallback to Mock strings.")
            
        return self

settings = Settings()
