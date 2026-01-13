"""Configuration settings for the application."""
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )
    
    # Environment
    ENV: str = "development"
    
    # Database - REQUIRED in production, optional in development
    # In production (AWS EB), DATABASE_URL must be set via environment variable
    # In development, if not set, will use default localhost (for docker-compose compatibility)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Database connection URL. REQUIRED in production."
    )
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:80"
    
    # Presence TTL (seconds)
    PRESENCE_TTL_SECONDS: int = 15
    
    @model_validator(mode="after")
    def validate_database_url(self) -> "Settings":
        """Validate DATABASE_URL is set, especially in production."""
        # If DATABASE_URL is None or empty, check if we're in production
        if not self.DATABASE_URL or self.DATABASE_URL.strip() == "":
            if self.ENV == "production":
                raise ValueError(
                    "DATABASE_URL is required in production. "
                    "Please set it as an environment variable in Elastic Beanstalk."
                )
            # In development, use default localhost for docker-compose compatibility
            self.DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test"
        return self


settings = Settings()

