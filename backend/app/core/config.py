"""
Core configuration settings using Pydantic Settings.
Loads environment variables and API keys.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Avocado TikTok Fact Checker"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Supadata API Configuration
    SUPADATA_API_KEY: str
    SUPADATA_BASE_URL: str = "https://api.supadata.ai/v1"
    SUPADATA_METADATA_ENDPOINT: str = "/metadata"
    SUPADATA_TRANSCRIPT_ENDPOINT: str = "/transcript"
    
    # Google Gemini API Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3-flash-preview"  # Latest Gemini 2.0 Flash
    GEMINI_TEMPERATURE: float = 0.3  # Lower temperature for more factual responses
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048
    GEMINI_USE_SEARCH: bool = True  # Enable Google Search grounding
    
    # Request Configuration
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0  # Initial retry delay in seconds
    RETRY_BACKOFF: float = 2.0  # Exponential backoff multiplier
    
    # Caching Configuration
    CACHE_TTL: int = 3600  # Cache time-to-live in seconds (1 hour)
    CACHE_MAX_SIZE: int = 1000  # Maximum number of cached items
    
    # CORS Configuration (for browser extension)
    CORS_ORIGINS: list[str] = ["*"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
