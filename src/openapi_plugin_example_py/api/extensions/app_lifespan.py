"""Application lifespan manager implementation."""
from typing import Optional

from fastapi import FastAPI
from openapi_plugin_common.lifespan.base_lifespan import BaseLifespanManager
from openapi_plugin_common.logging import BaseLogger, LoggerConfig
from openapi_plugin_common.logging.base_logger import LogLevel
from openapi_plugin_common.infrastructure.telemetry import AzureMonitorTelemetryService

from src.openapi_plugin_example_py.api.extensions.dependency_injection import setup_dependencies
from src.openapi_plugin_example_py.config import get_settings
from src.openapi_plugin_example_py.infrastructure.command_factory import CustomCommandInvokerFactory


class ExamplePluginLifespanManager(BaseLifespanManager):
    """Custom lifespan manager for Example Plugin."""
    
    async def startup(self, app: FastAPI) -> None:
        """Perform startup operations."""
        # Get settings
        settings = get_settings()
        
        # Initialize telemetry if enabled
        telemetry_service = None
        if settings.telemetry.enabled and settings.telemetry.connection_string:
            try:
                telemetry_service = AzureMonitorTelemetryService(
                    connection_string=settings.telemetry.connection_string,
                    service_name=settings.telemetry.service_name,
                    logger_name=settings.telemetry.logger_name
                )
                if self.logger:
                    self.logger.info("Telemetry service initialized")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to initialize telemetry: {e}")
        
        # Update telemetry service in the manager if initialized
        if telemetry_service:
            self.telemetry_service = telemetry_service
        
        # Store in app state
        app.state.settings = settings
        app.state.telemetry_service = telemetry_service
        
        # Setup dependencies to create services and handlers
        await setup_dependencies(app)
        
        # Debug logging
        if self.logger:
            self.logger.info(f"Settings loaded - environment: {settings.environment}")
            self.logger.info(f"Use filesystem storage: {settings.use_filesystem_storage}")
            self.logger.info(f"Filesystem storage path: {settings.filesystem_storage_path}")
            self.logger.info(f"Bypass auth: {settings.bypass_auth}")
            self.logger.info(f"OpenAI API key configured: {settings.plugin_options.openai is not None and settings.plugin_options.openai.api_key is not None}")
            self.logger.info(f"Azure OpenAI configured: {settings.plugin_options.azure_openai is not None}")
        
        # Create command factory with all services
        app.state.command_invoker_factory = CustomCommandInvokerFactory(
            telemetry_service=telemetry_service,
            cache_service=app.state.cache_service,
            blob_service=app.state.blob_service,
            llm_provider=app.state.llm_provider,
            enable_command_logging=True,
            session_id=None,
            user_id=None
        )
        
        if self.logger:
            self.logger.info(f"Blob service configured: {app.state.blob_service is not None}")
            self.logger.info(f"Blob service type: {type(app.state.blob_service)}")
            self.logger.info(f"LLM provider configured: {app.state.llm_provider is not None}")
            self.logger.info(f"Cache service configured: {app.state.cache_service is not None}")
    
    async def shutdown(self, app: FastAPI) -> None:
        """Perform shutdown operations."""
        # Custom shutdown logic if needed
        pass


def create_logger(telemetry_service: Optional[AzureMonitorTelemetryService] = None) -> BaseLogger:
    """Create a logger instance with the common logging system.
    
    Args:
        telemetry_service: Optional telemetry service for integrated logging
        
    Returns:
        Configured BaseLogger instance
    """
    settings = get_settings()
    
    # Configure log level based on environment
    log_level = LogLevel.DEBUG if settings.environment == "development" else LogLevel.INFO
    
    # Create logger configuration
    logger_config = LoggerConfig(
        name="openapi_plugin_example",
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create and return logger
    return BaseLogger(logger_config, telemetry_service)