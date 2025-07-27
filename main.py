"""Main application entry point."""
from fastapi import Depends, FastAPI
from openapi_plugin_common.lifespan import LifespanConfig, create_lifespan

from src.openapi_plugin_example_py.api.controllers import health_controller, plugin_controller
from src.openapi_plugin_example_py.api.extensions.app_lifespan import (
    ExamplePluginLifespanManager,
    create_logger,
)
from src.openapi_plugin_example_py.api.extensions.cors import configure_cors
from src.openapi_plugin_example_py.api.extensions.exception_handlers import configure_exception_handlers
from src.openapi_plugin_example_py.api.middlewares.telemetry import TelemetryMiddleware
from src.openapi_plugin_example_py.config import get_settings
from src.openapi_plugin_example_py.infrastructure.security import JWTBearer

# Create logger using the common logging system
logger = create_logger()

# Create lifespan configuration
lifespan_config = LifespanConfig(
    app_name="Example Plugin API",
    logger=logger,
    telemetry_service=None,  # Will be initialized in startup
    startup_hooks=[],
    shutdown_hooks=[],
    state_initializers={}
)

# Create lifespan using the factory with custom manager
lifespan = create_lifespan(lifespan_config, ExamplePluginLifespanManager)

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