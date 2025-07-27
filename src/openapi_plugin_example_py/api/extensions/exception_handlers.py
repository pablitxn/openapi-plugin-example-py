"""Global exception handlers."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openapi_plugin_common import ExceptionHandlerBase, ProblemDetailsFactory

from src.openapi_plugin_example_py.config import get_settings

logger = logging.getLogger(__name__)


def configure_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers for the application."""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        # Get settings
        settings = get_settings()
        
        # Log to telemetry if available
        if hasattr(app.state, "telemetry_service") and app.state.telemetry_service:
            exception_handler = ExceptionHandlerBase(
                logger=logger,
                telemetry_service=app.state.telemetry_service
            )
            exception_handler.log_exception(exc)
        
        # Create problem details
        problem = ProblemDetailsFactory.create_internal_server_error(
            detail=str(exc) if settings.environment == "development" else None,
            instance=str(request.url)
        )
        
        return JSONResponse(
            status_code=problem.status,
            content=problem.model_dump()
        )