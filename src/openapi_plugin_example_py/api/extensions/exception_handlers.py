"""Global exception handlers."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openapi_plugin_common import BaseExceptionHandler, BaseLogger, LoggerConfig

from src.openapi_plugin_example_py.config import get_settings

logger = logging.getLogger(__name__)


def configure_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers for the application."""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler using BaseExceptionHandler."""
        # Get settings
        settings = get_settings()
        
        # Get services from app state
        telemetry_service = getattr(app.state, "telemetry_service", None)
        base_logger = getattr(app.state, "logger", None)
        
        # Create base logger if not available
        if not base_logger:
            config = LoggerConfig(name="exception_handler")
            base_logger = BaseLogger(config, telemetry_service)
        
        # Create exception handler
        exception_handler = BaseExceptionHandler(
            telemetry_service=telemetry_service,
            logger=base_logger,
            include_stack_trace=settings.environment == "development"
        )
        
        # Extract request context
        correlation_id = request.headers.get("x-correlation-id")
        user_id = request.headers.get("x-user-id")
        
        # Handle the exception and get problem details
        problem = exception_handler.handle_exception(
            exception=exc,
            correlation_id=correlation_id,
            request_path=str(request.url),
            user_id=user_id,
            method=request.method,
            headers={k: v for k, v in request.headers.items() if k.lower().startswith("x-")}
        )
        
        return JSONResponse(
            status_code=problem.status,
            content=problem.model_dump(),
            headers={"X-Correlation-Id": correlation_id} if correlation_id else {}
        )