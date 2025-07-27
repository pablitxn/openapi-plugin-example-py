"""Sample command implementation."""
from __future__ import annotations

from typing import Optional

from openapi_plugin_common import CommandBase, CommandContextBase

from ..options import ExamplePluginOptions


class SampleCommandContext(CommandContextBase):
    """Context for the sample command."""
    
    sample_input: str
    use_cache: bool = True
    metadata: dict = {}


class SampleCommandResult:
    """Result from the sample command."""
    
    def __init__(self, sample_response: str, cached: bool = False):
        self.sample_response = sample_response
        self.cached = cached
        self.timestamp = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "sampleResponse": self.sample_response,
            "cached": self.cached,
            "timestamp": self.timestamp
        }


class SampleCommand(CommandBase[SampleCommandContext, ExamplePluginOptions]):
    """Command to process a sample request."""
    
    def __init__(
        self,
        telemetry_service: Optional[object] = None,
        cache_service: Optional[object] = None
    ) -> None:
        """Initialize the command."""
        super().__init__(telemetry_service)
        self._cache_service = cache_service
    
    async def execute_command_async(self, context: SampleCommandContext) -> None:
        """Execute the sample command logic."""
        # Check cache if enabled
        if context.use_cache and self._cache_service:
            cache_key = f"sample:{context.chat_id}:{hash(context.sample_input)}"
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                context.metadata["result"] = SampleCommandResult(
                    sample_response=cached_result,
                    cached=True
                )
                return
        
        # Process the sample input
        processed_result = await self._process_sample(context.sample_input)
        
        # Cache the result if enabled
        if context.use_cache and self._cache_service:
            await self._save_to_cache(cache_key, processed_result)
        
        # Store result in context metadata
        context.metadata["result"] = SampleCommandResult(
            sample_response=processed_result,
            cached=False
        )
    
    async def _process_sample(self, sample_input: str) -> str:
        """Process the sample input."""
        # This is where the actual business logic would go
        # For example, text processing, validation, transformation, etc.
        
        # Simple example: convert to uppercase and add prefix
        processed = f"Processed: {sample_input.upper()}"
        
        # Log if full tracking is enabled
        if self._is_enabled_full_tracking and self._telemetry_service:
            properties = {
                "InputLength": str(len(sample_input)),
                "ProcessedLength": str(len(processed))
            }
            if hasattr(self._telemetry_service, "log_event"):
                self._telemetry_service.log_event("SampleProcessed", properties)
        
        return processed
    
    async def _get_from_cache(self, key: str) -> Optional[str]:
        """Get value from cache."""
        if not self._cache_service:
            return None
        
        try:
            # Assuming cache service has async get method
            if hasattr(self._cache_service, "get"):
                return await self._cache_service.get(key)
        except Exception as e:
            if self._telemetry_service and hasattr(self._telemetry_service, "log_warning"):
                self._telemetry_service.log_warning(
                    f"Cache get failed: {str(e)}",
                    {"CacheKey": key, "Error": str(e)}
                )
        
        return None
    
    async def _save_to_cache(self, key: str, value: str) -> None:
        """Save value to cache."""
        if not self._cache_service:
            return
        
        try:
            # Assuming cache service has async set method
            if hasattr(self._cache_service, "set"):
                await self._cache_service.set(key, value, expire=3600)
        except Exception as e:
            if self._telemetry_service and hasattr(self._telemetry_service, "log_warning"):
                self._telemetry_service.log_warning(
                    f"Cache set failed: {str(e)}",
                    {"CacheKey": key, "Error": str(e)}
                )