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
        llm_provider: Optional[object] = None,
    ):
        """Initialize the factory with services."""
        super().__init__(telemetry_service)
        self._cache_service = cache_service
        self._blob_service = blob_service
        self._llm_provider = llm_provider
    
    def create(self, command_type: Type[CommandBase]) -> CommandBase:
        """Create command with appropriate services injected."""
        # Debug logging
        print(f"CustomCommandInvokerFactory.create called for: {command_type}")
        print(f"  - Blob service available: {self._blob_service is not None}")
        print(f"  - LLM provider available: {self._llm_provider is not None}")
        print(f"  - Cache service available: {self._cache_service is not None}")
        print(f"  - Telemetry service available: {self._telemetry_service is not None}")
        
        if command_type == SampleCommand:
            print("  -> Creating SampleCommand")
            return SampleCommand(
                telemetry_service=self._telemetry_service,
                cache_service=self._cache_service
            )
        elif command_type == BlobSampleCommand:
            print(f"  -> Creating BlobSampleCommand with blob_service={self._blob_service}")
            return BlobSampleCommand(
                telemetry_service=self._telemetry_service,
                blob_service=self._blob_service
            )
        elif command_type == AISampleCommand:
            print(f"  -> Creating AISampleCommand with llm_provider={self._llm_provider}")
            return AISampleCommand(
                telemetry_service=self._telemetry_service,
                cache_service=self._cache_service,
                llm_provider=self._llm_provider
            )
        elif command_type == CreatePlotCommand:
            print(f"  -> Creating CreatePlotCommand with blob_service={self._blob_service}")
            return CreatePlotCommand(
                telemetry_service=self._telemetry_service,
                blob_service=self._blob_service
            )
        else:
            print(f"  -> Fallback to parent implementation for {command_type}")
            # Fallback to parent implementation
            return super().create(command_type)