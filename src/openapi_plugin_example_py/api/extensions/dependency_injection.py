"""Dependency injection setup for the application."""
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, FastAPI, Request
from openapi_plugin_common import AzureBlobService

from ...business_logic.handlers import (
    AISampleHandler,
    BlobSampleHandler,
    CreatePlotHandler,
    SampleHandler,
)
from ...infrastructure.openai import OpenAIService
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


async def get_openai_service(request: Request):
    """Get OpenAI service."""
    app = request.app
    settings = app.state.settings
    if settings.plugin_options.openai and settings.plugin_options.openai.api_key:
        return OpenAIService(
            api_key=settings.plugin_options.openai.api_key,
            model=settings.plugin_options.openai.model,
            temperature=settings.plugin_options.openai.temperature,
            max_tokens=settings.plugin_options.openai.max_tokens,
            telemetry_service=app.state.telemetry_service
        )
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
    openai_service = Depends(get_openai_service)
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
    
    # Use filesystem storage in development/bypass mode
    if settings.use_filesystem_storage:
        from ...infrastructure.blob_storage.filesystem_service import FilesystemBlobService
        return FilesystemBlobService(settings.filesystem_storage_path)
    
    # Use Azure Blob Storage in production
    if settings.blob_storage and settings.blob_storage.connection_string:
        return AzureBlobService(settings.blob_storage.connection_string)
    return None


async def get_openai_service_for_app(app: FastAPI):
    """Get OpenAI service for app initialization."""
    settings = app.state.settings
    if settings.plugin_options.openai and settings.plugin_options.openai.api_key:
        return OpenAIService(
            api_key=settings.plugin_options.openai.api_key,
            model=settings.plugin_options.openai.model,
            temperature=settings.plugin_options.openai.temperature,
            max_tokens=settings.plugin_options.openai.max_tokens,
            telemetry_service=app.state.telemetry_service
        )
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
    app.state.openai_service = await get_openai_service_for_app(app)
    app.state.geney_client = await get_geney_client_for_app(app)