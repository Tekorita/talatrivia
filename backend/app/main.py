"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.infrastructure.api.routers import (
    admin,
    auth,
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend dev server
        "http://localhost:80",   # Frontend Docker (nginx on port 80)
    ],
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

