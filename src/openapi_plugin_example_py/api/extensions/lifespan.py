"""Application lifespan management."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from openapi_plugin_common import AzureMonitorTelemetryService

from src.openapi_plugin_example_py.api.extensions.dependency_injection import (
    setup_dependencies,
)
from src.openapi_plugin_example_py.config import get_settings
from src.openapi_plugin_example_py.infrastructure.command_factory import (
    CustomCommandInvokerFactory,
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
    logger.info(f"Azure OpenAI configured: {settings.plugin_options.azure_openai is not None}")
    
    # Create command factory with all services
    app.state.command_invoker_factory = CustomCommandInvokerFactory(
        telemetry_service=telemetry_service,
        cache_service=app.state.cache_service,
        blob_service=app.state.blob_service,
        llm_provider=app.state.llm_provider,
        enable_command_logging=True,  # Enable command event logging
        session_id=None,  # Will generate a UUID for the session
        user_id=None  # Can be set from auth context later
    ) # todo: check this shit
    
    logger.info("Example Plugin started successfully")
    logger.info(f"Blob service configured: {app.state.blob_service is not None}")
    logger.info(f"Blob service type: {type(app.state.blob_service)}")
    logger.info(f"LLM provider configured: {app.state.llm_provider is not None}")
    logger.info(f"Cache service configured: {app.state.cache_service is not None}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Example Plugin...")
    if telemetry_service:
        telemetry_service.flush()
    
    logger.info("Example Plugin shut down successfully")