"""AI sample request handler."""
import time
from typing import Optional

from openapi_plugin_common import CommandInvoker, RequestHandlerBase

from ..commands import AISampleCommand, AISampleCommandContext
from ..options import ExamplePluginOptions
from ..requests import AISampleRequest, AISampleResponse


class AISampleHandler(RequestHandlerBase[AISampleRequest, AISampleResponse]):
    """Handler for AI sample requests."""
    
    def __init__(
        self,
        command_invoker_factory,
        plugin_options: ExamplePluginOptions,
        telemetry_service: Optional[object] = None
    ) -> None:
        """Initialize the handler."""
        super().__init__(telemetry_service)
        self._command_invoker_factory = command_invoker_factory
        self._plugin_options = plugin_options
    
    async def execute_async(self, request: AISampleRequest) -> AISampleResponse:
        """Execute the AI sample request."""
        # Override options if provided in request
        if request.temperature is not None and self._plugin_options.openai:
            self._plugin_options.openai.temperature = request.temperature
        if request.max_tokens is not None and self._plugin_options.openai:
            self._plugin_options.openai.max_tokens = request.max_tokens
        
        # Create command context
        context = AISampleCommandContext(
            chat_id=request.chat_id,
            agent_id=request.agent_id,
            agent_version=request.agent_version,
            sample_prompt=request.sample_prompt,
            use_ai=request.use_ai,
            validate_schema=request.validate_schema
        )
        
        # Create and execute command
        command_invoker = self._command_invoker_factory.create(AISampleCommand)
        await command_invoker.invoke_async(context, self._plugin_options)
        
        # Get result from context metadata
        result = context.metadata.get("result")
        if not result:
            raise ValueError("Command did not produce a result")
        
        # Determine if response was cached
        cached = context.metadata.get("cached", False)
        
        # Create response
        return AISampleResponse(
            ai_response=result.ai_response,
            model_used=result.model_used,
            tokens_used=result.tokens_used,
            cached=cached
        )