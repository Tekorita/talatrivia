"""Configuration settings for the application."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )
    
    # Environment
    ENV: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://test:test@localhost/test"


settings = Settings()

