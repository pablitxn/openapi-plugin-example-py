"""Dependency injection setup for the application."""
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, FastAPI, Request
from openapi_plugin_common import AzureBlobService, create_llm_provider

from ...business_logic.handlers import (
    AISampleHandler,
    BlobSampleHandler,
    CreatePlotHandler,
    SampleHandler,
)
from ...infrastructure.security import GenEYClient


async def get_cache_service(request: Request):
    """Get cache service."""
    app = request.app
    settings = app.state.settings
    if settings.redis_url and settings.plugin_options.cache.enabled:
        try:
            return await redis.from_url(settings.redis_url)
        except Exception as e:
            # Log error but don't fail
            if app.state.telemetry_service:
                app.state.telemetry_service.log_warning(
                    f"Failed to connect to Redis: {e}"
                )
    return None


async def get_blob_service(request: Request):
    """Get blob service."""
    app = request.app
    settings = app.state.settings
    
    # Use filesystem storage in development/bypass mode
    if settings.use_filesystem_storage:
        from ...infrastructure.blob_storage.filesystem_service import FilesystemBlobService
        return FilesystemBlobService(settings.filesystem_storage_path)
    
    # Use Azure Blob Storage in production
    if settings.blob_storage and settings.blob_storage.connection_string:
        return AzureBlobService(settings.blob_storage.connection_string)
    return None


async def get_llm_provider(request: Request):
    """Get LLM provider service."""
    app = request.app
    settings = app.state.settings
    
    # Prefer Azure OpenAI if configured
    if settings.plugin_options.azure_openai:
        return create_llm_provider(
            config=settings.plugin_options.azure_openai,
            telemetry_service=app.state.telemetry_service
        )
    
    # Fall back to legacy OpenAI config if available
    elif settings.plugin_options.openai and settings.plugin_options.openai.api_key:
        # Note: This is deprecated - should migrate to Azure OpenAI
        if app.state.telemetry_service:
            app.state.telemetry_service.log_warning(
                "Using deprecated OpenAI configuration. Please migrate to Azure OpenAI."
            )
        # For backward compatibility, we would need to implement a direct OpenAI provider
        # For now, we'll return None and let the application handle it
        return None
    
    return None


async def get_geney_client(request: Request):
    """Get GenEY client."""
    app = request.app
    settings = app.state.settings
    if settings.security.geney_client_id and settings.security.geney_api_domain:
        return GenEYClient(
            allowed_file_types=settings.plugin_options.supported_file_types
        )
    return None


# Handler dependencies
async def get_sample_handler(
    request: Request,
    cache_service = Depends(get_cache_service)
) -> SampleHandler:
    """Get sample handler with dependencies."""
    app = request.app
    return SampleHandler(
        command_invoker_factory=app.state.command_invoker_factory,
        plugin_options=app.state.settings.plugin_options,
        telemetry_service=app.state.telemetry_service
    )


async def get_ai_sample_handler(
    request: Request,
    cache_service = Depends(get_cache_service),
    llm_provider = Depends(get_llm_provider)
) -> AISampleHandler:
    """Get AI sample handler with dependencies."""
    app = request.app
    return AISampleHandler(
        command_invoker_factory=app.state.command_invoker_factory,
        plugin_options=app.state.settings.plugin_options,
        telemetry_service=app.state.telemetry_service
    )


async def get_blob_sample_handler(
    request: Request,
    blob_service = Depends(get_blob_service)
) -> BlobSampleHandler:
    """Get blob sample handler with dependencies."""
    app = request.app
    return BlobSampleHandler(
        command_invoker_factory=app.state.command_invoker_factory,
        plugin_options=app.state.settings.plugin_options,
        telemetry_service=app.state.telemetry_service
    )


async def get_create_plot_handler(
    request: Request,
    blob_service = Depends(get_blob_service)
) -> CreatePlotHandler:
    """Get create plot handler with dependencies."""
    app = request.app
    return CreatePlotHandler(
        command_invoker_factory=app.state.command_invoker_factory,
        plugin_options=app.state.settings.plugin_options,
        telemetry_service=app.state.telemetry_service
    )


async def get_cache_service_for_app(app: FastAPI):
    """Get cache service for app initialization."""
    settings = app.state.settings
    if settings.redis_url and settings.plugin_options.cache.enabled:
        try:
            return await redis.from_url(settings.redis_url)
        except Exception as e:
            # Log error but don't fail
            if app.state.telemetry_service:
                app.state.telemetry_service.log_warning(
                    f"Failed to connect to Redis: {e}"
                )
    return None


async def get_blob_service_for_app(app: FastAPI):
    """Get blob service for app initialization."""
    settings = app.state.settings
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Getting blob service - use_filesystem_storage: {settings.use_filesystem_storage}")
    logger.info(f"Filesystem storage path: {settings.filesystem_storage_path}")
    
    # Use filesystem storage in development/bypass mode
    if settings.use_filesystem_storage:
        from ...infrastructure.blob_storage.filesystem_service import FilesystemBlobService
        service = FilesystemBlobService(settings.filesystem_storage_path)
        logger.info(f"Created FilesystemBlobService at path: {settings.filesystem_storage_path}")
        return service
    
    # Use Azure Blob Storage in production
    if settings.blob_storage and settings.blob_storage.connection_string:
        service = AzureBlobService(settings.blob_storage.connection_string)
        logger.info("Created AzureBlobService")
        return service
    
    logger.warning("No blob service configured!")
    return None


async def get_llm_provider_for_app(app: FastAPI):
    """Get LLM provider service for app initialization."""
    settings = app.state.settings
    
    # Prefer Azure OpenAI if configured
    if settings.plugin_options.azure_openai:
        return create_llm_provider(
            config=settings.plugin_options.azure_openai,
            telemetry_service=app.state.telemetry_service
        )
    
    # Fall back to legacy OpenAI config if available
    elif settings.plugin_options.openai and settings.plugin_options.openai.api_key:
        # Note: This is deprecated - should migrate to Azure OpenAI
        if app.state.telemetry_service:
            app.state.telemetry_service.log_warning(
                "Using deprecated OpenAI configuration. Please migrate to Azure OpenAI."
            )
        # For backward compatibility, we would need to implement a direct OpenAI provider
        # For now, we'll return None and let the application handle it
        return None
    
    return None


async def get_geney_client_for_app(app: FastAPI):
    """Get GenEY client for app initialization."""
    settings = app.state.settings
    if settings.security.geney_client_id and settings.security.geney_api_domain:
        return GenEYClient(
            allowed_file_types=settings.plugin_options.supported_file_types
        )
    return None


async def setup_dependencies(app: FastAPI):
    """Setup application dependencies."""
    # Override dependencies for handlers
    app.dependency_overrides[SampleHandler] = get_sample_handler
    app.dependency_overrides[AISampleHandler] = get_ai_sample_handler
    app.dependency_overrides[BlobSampleHandler] = get_blob_sample_handler
    app.dependency_overrides[CreatePlotHandler] = get_create_plot_handler
    
    # Store services in app state for commands
    app.state.cache_service = await get_cache_service_for_app(app)
    app.state.blob_service = await get_blob_service_for_app(app)
    app.state.llm_provider = await get_llm_provider_for_app(app)
    app.state.geney_client = await get_geney_client_for_app(app)