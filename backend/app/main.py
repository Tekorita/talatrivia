"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging import setup_logging
from app.infrastructure.api.routers import gameplay, health, lobby

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

# Register routers
app.include_router(health.router)
app.include_router(lobby.router)
app.include_router(gameplay.router)

