"""Sample request handler."""
from typing import Optional

from .base_plugin_handler import BasePluginHandler
from openapi_plugin_common import BaseLogger

from ..commands import SampleCommand, SampleCommandContext
from ..options import ExamplePluginOptions
from ..requests import SampleRequest, SampleResponse


class SampleHandler(BasePluginHandler[SampleRequest, SampleResponse]):
    """Handler for sample requests."""
    
    def __init__(
        self,
        command_invoker_factory,
        plugin_options: ExamplePluginOptions,
        telemetry_service: Optional[object] = None,
        logger: Optional[BaseLogger] = None
    ) -> None:
        """Initialize the handler."""
        super().__init__(command_invoker_factory, plugin_options, telemetry_service, logger)
    
    async def _process_async(
        self,
        request: SampleRequest,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> SampleResponse:
        """Process the sample request.
        
        The base handler already tracks timing and telemetry.
        """
        # Create command context
        context = SampleCommandContext(
            chat_id=request.chat_id,
            agent_id=request.agent_id,
            agent_version=request.agent_version,
            sample_input=request.sample_input,
            use_cache=request.use_cache
        )
        
        # Execute command
        await self.execute_command_async(SampleCommand, context)
        
        # Get result from context metadata
        result = context.metadata.get("result")
        if not result:
            raise ValueError("Command did not produce a result")
        
        # Create response - base handler tracks the timing
        return SampleResponse(
            sample_response=result.sample_response,
            cached=result.cached,
            processing_time_ms=0  # Will be set by the controller
        ) # todo: fix this shit ^