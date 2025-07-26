"""Dependency injection setup for the application."""
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, FastAPI
from openapi_plugin_common import AzureBlobService

from ...business_logic.handlers import (
    AISampleHandler,
    BlobSampleHandler,
    CreatePlotHandler,
    SampleHandler,
)
from ...infrastructure.openai import OpenAIService
from ...infrastructure.security import GenEYClient


async def get_cache_service(app: FastAPI):
    """Get cache service."""
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


async def get_blob_service(app: FastAPI):
    """Get blob service."""
    settings = app.state.settings
    if settings.blob_storage and settings.blob_storage.connection_string:
        return AzureBlobService(settings.blob_storage.connection_string)
    return None


async def get_openai_service(app: FastAPI):
    """Get OpenAI service."""
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


async def get_geney_client(app: FastAPI):
    """Get GenEY client."""
    settings = app.state.settings
    if settings.security.geney_client_id and settings.security.geney_api_domain:
        return GenEYClient(
            client_id=settings.security.client_id,
            tenant_id=settings.security.tenant_id,
            geney_client_id=settings.security.geney_client_id,
            geney_api_domain=settings.security.geney_api_domain
        )
    return None


# Handler dependencies
async def get_sample_handler(
    app: FastAPI = Depends(lambda: app),
    cache_service = Depends(get_cache_service)
) -> SampleHandler:
    """Get sample handler with dependencies."""
    return SampleHandler(
        command_invoker_factory=app.state.command_invoker_factory,
        plugin_options=app.state.settings.plugin_options,
        telemetry_service=app.state.telemetry_service
    )


async def get_ai_sample_handler(
    app: FastAPI = Depends(lambda: app),
    cache_service = Depends(get_cache_service),
    openai_service = Depends(get_openai_service)
) -> AISampleHandler:
    """Get AI sample handler with dependencies."""
    return AISampleHandler(
        command_invoker_factory=app.state.command_invoker_factory,
        plugin_options=app.state.settings.plugin_options,
        telemetry_service=app.state.telemetry_service
    )


async def get_blob_sample_handler(
    app: FastAPI = Depends(lambda: app),
    blob_service = Depends(get_blob_service)
) -> BlobSampleHandler:
    """Get blob sample handler with dependencies."""
    return BlobSampleHandler(
        command_invoker_factory=app.state.command_invoker_factory,
        plugin_options=app.state.settings.plugin_options,
        telemetry_service=app.state.telemetry_service
    )


async def get_create_plot_handler(
    app: FastAPI = Depends(lambda: app),
    blob_service = Depends(get_blob_service)
) -> CreatePlotHandler:
    """Get create plot handler with dependencies."""
    return CreatePlotHandler(
        command_invoker_factory=app.state.command_invoker_factory,
        plugin_options=app.state.settings.plugin_options,
        telemetry_service=app.state.telemetry_service
    )


async def setup_dependencies(app: FastAPI):
    """Setup application dependencies."""
    # Override dependencies for handlers
    app.dependency_overrides[SampleHandler] = get_sample_handler
    app.dependency_overrides[AISampleHandler] = get_ai_sample_handler
    app.dependency_overrides[BlobSampleHandler] = get_blob_sample_handler
    app.dependency_overrides[CreatePlotHandler] = get_create_plot_handler
    
    # Store services in app state for commands
    app.state.cache_service = await get_cache_service(app)
    app.state.blob_service = await get_blob_service(app)
    app.state.openai_service = await get_openai_service(app)
    app.state.geney_client = await get_geney_client(app)