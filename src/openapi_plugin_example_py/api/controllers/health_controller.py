"""Health and system status endpoints."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["System"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    from main import app
    
    return {
        "status": "healthy",
        "service": "ExamplePlugin",
        "version": "1.0.0",
        "telemetry_enabled": app.state.telemetry_service is not None
    }


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Example Plugin API",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health"
    }