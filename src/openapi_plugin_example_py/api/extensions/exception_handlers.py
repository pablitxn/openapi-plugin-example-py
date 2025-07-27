"""Global exception handlers."""
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openapi_plugin_common import BaseLogger, LoggerConfig

from src.openapi_plugin_example_py.config import get_settings

logger = logging.getLogger(__name__)


def configure_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers for the application."""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler."""
        # Get settings
        settings = get_settings()
        
        # Get services from app state
        base_logger = getattr(app.state, "logger", None)
        
        # Create base logger if not available
        if not base_logger:
            config = LoggerConfig(name="exception_handler")
            base_logger = BaseLogger(config, None)
        
        # Extract request context
        correlation_id = request.headers.get("x-correlation-id", "")
        
        # Log the error
        base_logger.error(
            f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
            extra={
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "request_path": str(request.url),
                "request_method": request.method,
                "correlation_id": correlation_id
            }
        )
        
        # Create response content
        content = {
            "type": "https://tools.ietf.org/html/rfc7231#section-6.6.1",
            "title": "Internal Server Error",
            "status": 500,
            "detail": str(exc) if settings.environment == "development" else "An error occurred while processing your request.",
            "instance": str(request.url)
        }
        
        # Add stack trace in development
        if settings.environment == "development":
            content["stackTrace"] = traceback.format_exc()
        
        return JSONResponse(
            status_code=500,
            content=content,
            headers={"X-Correlation-Id": correlation_id} if correlation_id else {}
        )