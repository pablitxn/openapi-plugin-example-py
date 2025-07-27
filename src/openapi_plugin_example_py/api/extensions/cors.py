"""CORS configuration module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.openapi_plugin_example_py.config import get_settings


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware for the application."""
    settings = get_settings()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )