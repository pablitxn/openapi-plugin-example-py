"""Main application entry point."""
from fastapi import Depends, FastAPI

from src.openapi_plugin_example_py.api.controllers import health_controller, plugin_controller
from src.openapi_plugin_example_py.api.extensions.cors import configure_cors
from src.openapi_plugin_example_py.api.extensions.exception_handlers import configure_exception_handlers
from src.openapi_plugin_example_py.api.extensions.lifespan import lifespan
from src.openapi_plugin_example_py.api.extensions.logging import configure_logging
from src.openapi_plugin_example_py.api.middlewares.telemetry import TelemetryMiddleware
from src.openapi_plugin_example_py.config import get_settings
from src.openapi_plugin_example_py.infrastructure.security import JWTBearer

# Configure logging
logger = configure_logging()

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

# Configure middleware
configure_cors(app)
app.add_middleware(TelemetryMiddleware)

# Configure exception handlers
configure_exception_handlers(app)

# Configure routers
settings = get_settings()
auth_dependency = JWTBearer(api_audience=settings.security.api_audience)

# Protected routes
app.include_router(
    plugin_controller.router,
    prefix=f"{settings.api_prefix}/{settings.api_version}",
    dependencies=[Depends(auth_dependency)]
)

# Public routes
app.include_router(health_controller.router)


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