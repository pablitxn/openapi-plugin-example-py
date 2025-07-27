"""Main application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openapi_plugin_common import (
    AzureMonitorTelemetryService,
    CommandInvokerFactory,
    ExceptionHandlerBase,
    ProblemDetailsFactory,
)

from src.openapi_plugin_example_py.api.controllers import plugin_controller
from src.openapi_plugin_example_py.api.extensions.dependency_injection import (
    setup_dependencies,
)
from src.openapi_plugin_example_py.api.middlewares.telemetry import (
    TelemetryMiddleware,
)
from src.openapi_plugin_example_py.config import get_settings
from src.openapi_plugin_example_py.infrastructure.command_factory import (
    CustomCommandInvokerFactory,
)
from src.openapi_plugin_example_py.infrastructure.security import JWTBearer
from src.openapi_plugin_example_py.infrastructure.security.mock_auth import MockJWTBearer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting up Example Plugin...")
    
    # Get settings
    settings = get_settings()
    
    # Initialize telemetry
    telemetry_service = None
    if settings.telemetry.enabled and settings.telemetry.connection_string:
        try:
            telemetry_service = AzureMonitorTelemetryService(
                connection_string=settings.telemetry.connection_string,
                service_name=settings.telemetry.service_name,
                logger_name=settings.telemetry.logger_name
            )
            logger.info("Telemetry service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize telemetry: {e}")
    
    # Store in app state
    app.state.settings = settings
    app.state.telemetry_service = telemetry_service
    
    # Setup dependencies to create services and handlers
    await setup_dependencies(app)
    
    # Debug logging
    logger.info(f"Settings loaded - environment: {settings.environment}")
    logger.info(f"Use filesystem storage: {settings.use_filesystem_storage}")
    logger.info(f"Filesystem storage path: {settings.filesystem_storage_path}")
    logger.info(f"Bypass auth: {settings.bypass_auth}")
    logger.info(f"OpenAI API key configured: {settings.plugin_options.openai is not None and settings.plugin_options.openai.api_key is not None}")
    
    # Create command factory with all services
    app.state.command_invoker_factory = CustomCommandInvokerFactory(
        telemetry_service=telemetry_service,
        cache_service=app.state.cache_service,
        blob_service=app.state.blob_service,
        openai_service=app.state.openai_service
    )
    
    logger.info("Example Plugin started successfully")
    logger.info(f"Blob service configured: {app.state.blob_service is not None}")
    logger.info(f"Blob service type: {type(app.state.blob_service)}")
    logger.info(f"OpenAI service configured: {app.state.openai_service is not None}")
    logger.info(f"Cache service configured: {app.state.cache_service is not None}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Example Plugin...")
    if telemetry_service:
        telemetry_service.flush()
    
    logger.info("Example Plugin shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="Example Plugin API",
    description="Example OpenAPI plugin demonstrating command/handler pattern with authentication",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add telemetry middleware
app.add_middleware(TelemetryMiddleware)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
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


# Include routers
from fastapi import Depends

# Choose authentication based on bypass setting
auth_dependency = (
    MockJWTBearer() if settings.bypass_auth 
    else JWTBearer(api_audience=settings.security.api_audience)
)

app.include_router(
    plugin_controller.router,
    prefix=f"{settings.api_prefix}/{settings.api_version}",
    dependencies=[Depends(auth_dependency)]
)

# Health check endpoint (no auth required)
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ExamplePlugin",
        "version": "1.0.0",
        "telemetry_enabled": app.state.telemetry_service is not None
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Example Plugin API",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run with reload in development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level="info"
    )