"""Sample request handler."""
import time
from typing import Optional

from openapi_plugin_common import CommandInvoker, RequestHandlerBase

from ..commands import SampleCommand, SampleCommandContext
from ..options import ExamplePluginOptions
from ..requests import SampleRequest, SampleResponse


class SampleHandler(RequestHandlerBase[SampleRequest, SampleResponse]):
    """Handler for sample requests."""
    
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
    
    async def execute_async(self, request: SampleRequest) -> SampleResponse:
        """Execute the sample request."""
        start_time = time.time()
        
        # Create command context
        context = SampleCommandContext(
            chat_id=request.chat_id,
            agent_id=request.agent_id,
            agent_version=request.agent_version,
            sample_input=request.sample_input,
            use_cache=request.use_cache
        )
        
        # Create and execute command
        command_invoker = self._command_invoker_factory.create(SampleCommand)
        await command_invoker.invoke_async(context, self._plugin_options)
        
        # Get result from context metadata
        result = context.metadata.get("result")
        if not result:
            raise ValueError("Command did not produce a result")
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Create response
        return SampleResponse(
            sample_response=result.sample_response,
            cached=result.cached,
            processing_time_ms=processing_time_ms
        )