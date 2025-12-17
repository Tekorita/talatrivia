"""FastAPI application entry point."""
from fastapi import FastAPI
from app.core.logging import setup_logging
from app.infrastructure.api.routers import gameplay, health, lobby

# Setup logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title="TalaTrivia API",
    description="Backend API for TalaTrivia game",
    version="1.0.0",
)

# Register routers
app.include_router(health.router)
app.include_router(lobby.router)
app.include_router(gameplay.router)


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("TalaTrivia API starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("TalaTrivia API shutting down...")

