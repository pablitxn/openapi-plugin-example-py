"""AI sample command implementation."""
import json
import time
import uuid
from typing import List, Optional

from openapi_plugin_common import (
    CommandBase,
    CommandContextBase,
    CommandException,
    ConfigurationException,
    ValidationException,
    LLMProvider,
)

from ..options import ExamplePluginOptions


class AISampleCommandContext(CommandContextBase):
    """Context for the AI sample command."""
    
    messages: List[dict]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    stop: Optional[List[str]] = None
    user: Optional[str] = None
    metadata: dict = {}


class AISampleCommandResult:
    """Result from the AI sample command."""
    
    def __init__(
        self,
        id: str,
        model: str,
        content: str,
        finish_reason: str = "stop",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        created: Optional[int] = None
    ):
        self.id = id
        self.model = model
        self.content = content
        self.finish_reason = finish_reason
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.created = created or int(time.time())


class AISampleCommand(CommandBase[AISampleCommandContext, ExamplePluginOptions]):
    """Command to process an AI sample request."""
    
    def __init__(
        self,
        telemetry_service: Optional[object] = None,
        llm_provider: Optional[LLMProvider] = None,
        cache_service: Optional[object] = None
    ) -> None:
        """Initialize the command."""
        super().__init__(telemetry_service)
        self._llm_provider = llm_provider
        self._cache_service = cache_service
    
    async def execute_command_async(self, context: AISampleCommandContext) -> None:
        """Execute the AI sample command logic."""
        # Check if AI service is available
        if not self._llm_provider:
            raise ConfigurationException("LLM provider is not configured")
        
        # Create cache key from messages
        messages_str = json.dumps(context.messages, sort_keys=True)
        cache_key = f"ai_sample:{context.chat_id}:{hash(messages_str)}"
        
        # Check cache first
        if self._cache_service:
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                context.metadata["result"] = AISampleCommandResult(
                    id=cached_result["id"],
                    model=cached_result["model"],
                    content=cached_result["content"],
                    finish_reason=cached_result.get("finish_reason", "stop"),
                    prompt_tokens=cached_result.get("prompt_tokens", 0),
                    completion_tokens=cached_result.get("completion_tokens", 0),
                    total_tokens=cached_result.get("total_tokens", 0),
                    created=cached_result.get("created")
                )
                context.metadata["cached"] = True
                return
        
        # Process with AI
        result = await self._process_with_ai(context)
        
        # Cache the result
        if self._cache_service:
            await self._save_to_cache(cache_key, {
                "id": result.id,
                "model": result.model,
                "content": result.content,
                "finish_reason": result.finish_reason,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.total_tokens,
                "created": result.created
            })
        
        # Store result in context metadata
        context.metadata["result"] = result
        context.metadata["cached"] = False
    
    async def _process_with_ai(self, context: AISampleCommandContext) -> AISampleCommandResult:
        """Process the request using AI."""
        try:
            # Extract system and user messages
            system_messages = [msg for msg in context.messages if msg["role"] == "system"]
            user_messages = [msg for msg in context.messages if msg["role"] in ["user", "assistant"]]
            
            # Get system prompt (use first system message or default)
            system_prompt = system_messages[0]["content"] if system_messages else "You are a helpful AI assistant."
            
            # Format conversation for LLM provider
            # For now, we'll concatenate the conversation history
            conversation = []
            for msg in user_messages:
                conversation.append(f"{msg['role'].title()}: {msg['content']}")
            user_prompt = "\n".join(conversation)
            
            # Override model and parameters if provided
            if context.model:
                # This would need to be implemented in the LLM provider
                pass
            
            # Call LLM provider with additional parameters
            kwargs = {}
            if context.temperature is not None:
                kwargs["temperature"] = context.temperature
            if context.max_tokens is not None:
                kwargs["max_tokens"] = context.max_tokens
            if context.top_p is not None:
                kwargs["top_p"] = context.top_p
            if context.presence_penalty is not None:
                kwargs["presence_penalty"] = context.presence_penalty
            if context.frequency_penalty is not None:
                kwargs["frequency_penalty"] = context.frequency_penalty
            if context.stop:
                kwargs["stop"] = context.stop
            
            response = await self._llm_provider.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                chat_id=context.chat_id,
                **kwargs
            )
            
            # Generate completion ID
            completion_id = f"chatcmpl-{uuid.uuid4().hex[:16]}"
            
            # Log telemetry
            if self._telemetry_service and hasattr(self._telemetry_service, "log_event"):
                self._telemetry_service.log_event("AIProcessingCompleted", {
                    "ChatId": context.chat_id,
                    "Model": response.model,
                    "TotalTokens": str(response.usage.get("total_tokens", 0))
                })
            
            return AISampleCommandResult(
                id=completion_id,
                model=response.model or context.model or "unknown",
                content=response.content,
                finish_reason="stop",
                prompt_tokens=response.usage.get("prompt_tokens", 0),
                completion_tokens=response.usage.get("completion_tokens", 0),
                total_tokens=response.usage.get("total_tokens", 0)
            )
            
        except Exception as e:
            if self._telemetry_service and hasattr(self._telemetry_service, "log_error"):
                self._telemetry_service.log_error(
                    f"AI processing failed: {str(e)}",
                    {"Error": str(e), "ChatId": context.chat_id}
                )
            raise CommandException(f"AI processing failed: {str(e)}") from e
    
    async def _process_without_ai(self, messages: List[dict]) -> AISampleCommandResult:
        """Process without AI (fallback)."""
        # Simple fallback logic
        last_user_message = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "No user message")
        response = f"Fallback response for: {last_user_message}"
        
        completion_id = f"chatcmpl-fallback-{uuid.uuid4().hex[:16]}"
        
        return AISampleCommandResult(
            id=completion_id,
            model="fallback",
            content=response,
            finish_reason="stop",
            prompt_tokens=len(last_user_message.split()),
            completion_tokens=len(response.split()),
            total_tokens=len(last_user_message.split()) + len(response.split())
        )
    
    def _validate_response_schema(self, response) -> None:
        """Validate the AI response against schema."""
        # Simple validation - in real implementation would use JSON Schema
        if not hasattr(response, "content") or not response.content:
            raise ValidationException("AI response missing 'content' field")
    
    async def _get_from_cache(self, key: str) -> Optional[dict]:
        """Get value from cache."""
        if not self._cache_service:
            return None
        
        try:
            if hasattr(self._cache_service, "get"):
                cached = await self._cache_service.get(key)
                if cached:
                    return json.loads(cached) if isinstance(cached, str) else cached
        except Exception:
            pass
        
        return None
    
    async def _save_to_cache(self, key: str, value: dict) -> None:
        """Save value to cache."""
        if not self._cache_service:
            return
        
        try:
            if hasattr(self._cache_service, "set"):
                await self._cache_service.set(
                    key,
                    json.dumps(value),
                    expire=3600
                )
        except Exception:
            pass