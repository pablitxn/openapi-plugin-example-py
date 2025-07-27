"""AI sample request handler."""
from typing import Optional

from .base_plugin_handler import BasePluginHandler
from openapi_plugin_common import BaseLogger
from ..commands import AISampleCommand, AISampleCommandContext
from ..options import ExamplePluginOptions
from ..requests import AISampleRequest, AISampleResponse, ChatChoice, ChatMessage, Usage


class AISampleHandler(BasePluginHandler[AISampleRequest, AISampleResponse]):
    """Handler for AI sample requests."""
    
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
        request: AISampleRequest,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> AISampleResponse:
        """Process the AI sample request."""
        # Convert ChatMessage objects to dictionaries for the command
        messages = [msg.model_dump() for msg in request.messages]
        
        # Create command context
        context = AISampleCommandContext(
            chat_id=request.chat_id,
            agent_id=request.agent_id,
            agent_version=request.agent_version,
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            presence_penalty=request.presence_penalty,
            frequency_penalty=request.frequency_penalty,
            stop=request.stop if isinstance(request.stop, list) else [request.stop] if request.stop else None,
            user=request.user
        )
        
        # Execute command
        await self.execute_command_async(AISampleCommand, context)
        
        # Get result from context metadata
        result = context.metadata.get("result")
        if not result:
            raise ValueError("Command did not produce a result")
        
        # Determine if response was cached
        cached = context.metadata.get("cached", False)
        
        # Create response in OpenAI format
        return AISampleResponse(
            id=result.id,
            object="chat.completion",
            created=result.created,
            model=result.model,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=result.content
                    ),
                    finish_reason=result.finish_reason
                )
            ],
            usage=Usage(
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                total_tokens=result.total_tokens
            ),
            cached=cached
        )