"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.infrastructure.api.routers import (
    admin,
    auth,
    events,
    gameplay,
    health,
    lobby,
    play,
    questions,
    trivias,
    users,
)

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler."""
    # Startup
    logger.info("TalaTrivia API starting up...")
    yield
    # Shutdown
    logger.info("TalaTrivia API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="TalaTrivia API",
    description="Backend API for TalaTrivia game",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
# Read CORS_ORIGINS from environment variable (comma-separated list)
# Default to localhost for development

cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else []
# Strip whitespace from each origin
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(questions.router)
app.include_router(trivias.router)
app.include_router(admin.router)
app.include_router(play.router)
app.include_router(lobby.router)
app.include_router(gameplay.router)
app.include_router(events.router)

