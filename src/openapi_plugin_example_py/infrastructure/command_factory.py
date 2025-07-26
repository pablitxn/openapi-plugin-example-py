"""Custom command factory for dependency injection."""
from typing import Optional, Type

from openapi_plugin_common import CommandBase, CommandInvokerFactory

from ..business_logic.commands import (
    AISampleCommand,
    BlobSampleCommand,
    CreatePlotCommand,
    SampleCommand,
)


class CustomCommandInvokerFactory(CommandInvokerFactory):
    """Custom command invoker factory with service injection."""
    
    def __init__(
        self,
        telemetry_service: Optional[object] = None,
        cache_service: Optional[object] = None,
        blob_service: Optional[object] = None,
        openai_service: Optional[object] = None,
    ):
        """Initialize the factory with services."""
        super().__init__(telemetry_service)
        self._cache_service = cache_service
        self._blob_service = blob_service
        self._openai_service = openai_service
    
    def create(self, command_type: Type[CommandBase]) -> CommandBase:
        """Create command with appropriate services injected."""
        # Create base command with telemetry
        if command_type == SampleCommand:
            return SampleCommand(
                telemetry_service=self._telemetry_service,
                cache_service=self._cache_service
            )
        elif command_type == BlobSampleCommand:
            return BlobSampleCommand(
                telemetry_service=self._telemetry_service,
                blob_service=self._blob_service
            )
        elif command_type == AISampleCommand:
            return AISampleCommand(
                telemetry_service=self._telemetry_service,
                cache_service=self._cache_service,
                openai_service=self._openai_service
            )
        elif command_type == CreatePlotCommand:
            return CreatePlotCommand(
                telemetry_service=self._telemetry_service,
                blob_service=self._blob_service
            )
        else:
            # Fallback to parent implementation
            return super().create(command_type)