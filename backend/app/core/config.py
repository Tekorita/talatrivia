"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    ENV: str = "development"
    
    # Database
    DATABASE_URL: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

