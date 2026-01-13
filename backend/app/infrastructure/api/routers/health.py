"""Health check router."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.infrastructure.db.session import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """
    Basic health check endpoint.
    Returns quickly without database connection check.
    """
    return {"status": "ok"}


@router.get("/db")
async def health_check_db():
    """
    Database health check endpoint.
    Verifies database connectivity by executing a simple query.
    """
    try:
        # Execute a simple query to verify database connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )

