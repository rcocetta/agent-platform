"""
Health check API endpoints
"""
from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns the current status of the application
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "service": settings.app_name,
        "environment": settings.environment,
        "version": "1.0.0"
    }