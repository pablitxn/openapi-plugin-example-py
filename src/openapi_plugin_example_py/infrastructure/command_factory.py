"""Custom command factory for dependency injection."""
from typing import Optional, Type
import uuid

from openapi_plugin_common import CommandBase, CommandInvokerFactory
from openapi_plugin_common.log_events import CommandEventLogger, LoggedCommandWrapper

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
        enable_command_logging: bool = True,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Initialize the factory with services."""
        super().__init__(telemetry_service)
        self._cache_service = cache_service
        self._blob_service = blob_service
        self._llm_provider = llm_provider
        self._enable_command_logging = enable_command_logging
        self._session_id = session_id or str(uuid.uuid4())
        self._user_id = user_id
        
        # Initialize command event logger if logging is enabled
        self._command_event_logger = CommandEventLogger(
            telemetry_service=telemetry_service
        ) if enable_command_logging else None
    
    def create(self, command_type: Type[CommandBase]) -> CommandBase:
        """Create command with appropriate services injected."""
        # Debug logging
        print(f"CustomCommandInvokerFactory.create called for: {command_type}")
        print(f"  - Blob service available: {self._blob_service is not None}")
        print(f"  - LLM provider available: {self._llm_provider is not None}")
        print(f"  - Cache service available: {self._cache_service is not None}")
        print(f"  - Telemetry service available: {self._telemetry_service is not None}")
        print(f"  - Command logging enabled: {self._enable_command_logging}")
        
        # Create the base command instance
        command_instance = None
        
        if command_type == SampleCommand:
            print("  -> Creating SampleCommand")
            command_instance = SampleCommand(
                telemetry_service=self._telemetry_service,
                cache_service=self._cache_service
            )
        elif command_type == BlobSampleCommand:
            print(f"  -> Creating BlobSampleCommand with blob_service={self._blob_service}")
            command_instance = BlobSampleCommand(
                telemetry_service=self._telemetry_service,
                blob_service=self._blob_service
            )
        elif command_type == AISampleCommand:
            print(f"  -> Creating AISampleCommand with llm_provider={self._llm_provider}")
            command_instance = AISampleCommand(
                telemetry_service=self._telemetry_service,
                cache_service=self._cache_service,
                llm_provider=self._llm_provider
            )
        elif command_type == CreatePlotCommand:
            print(f"  -> Creating CreatePlotCommand with blob_service={self._blob_service}")
            command_instance = CreatePlotCommand(
                telemetry_service=self._telemetry_service,
                blob_service=self._blob_service
            )
        else:
            print(f"  -> Fallback to parent implementation for {command_type}")
            # Fallback to parent implementation
            command_instance = super().create(command_type)
        
        # Wrap with logging if enabled
        if self._enable_command_logging and self._command_event_logger and command_instance:
            print(f"  -> Wrapping command with event logging")
            correlation_id = str(uuid.uuid4())
            return LoggedCommandWrapper(
                command=command_instance,
                event_logger=self._command_event_logger,
                correlation_id=correlation_id,
                user_id=self._user_id,
                session_id=self._session_id
            )
        
        return command_instance