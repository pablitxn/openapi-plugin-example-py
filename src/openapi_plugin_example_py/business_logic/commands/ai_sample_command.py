"""AI sample command implementation."""
import json
from typing import Optional

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
    
    sample_prompt: str
    use_ai: bool = True
    validate_schema: bool = True
    metadata: dict = {}


class AISampleCommandResult:
    """Result from the AI sample command."""
    
    def __init__(
        self,
        ai_response: str,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None
    ):
        self.ai_response = ai_response
        self.model_used = model_used
        self.tokens_used = tokens_used
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "aiResponse": self.ai_response,
            "modelUsed": self.model_used,
            "tokensUsed": self.tokens_used
        }


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
        if not self._llm_provider and context.use_ai:
            raise ConfigurationException("LLM provider is not configured")
        
        # Check cache first
        cache_key = f"ai_sample:{context.chat_id}:{hash(context.sample_prompt)}"
        if self._cache_service:
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                context.metadata["result"] = AISampleCommandResult(
                    ai_response=cached_result["response"],
                    model_used=cached_result.get("model"),
                    tokens_used=cached_result.get("tokens")
                )
                return
        
        # Process with AI
        if context.use_ai and self._llm_provider:
            result = await self._process_with_ai(context)
        else:
            # Fallback to non-AI processing
            result = await self._process_without_ai(context.sample_prompt)
        
        # Cache the result
        if self._cache_service:
            await self._save_to_cache(cache_key, {
                "response": result.ai_response,
                "model": result.model_used,
                "tokens": result.tokens_used
            })
        
        # Store result in context metadata
        context.metadata["result"] = result
    
    async def _process_with_ai(self, context: AISampleCommandContext) -> AISampleCommandResult:
        """Process the request using AI."""
        try:
            # Get prompts configuration
            system_prompt = "You are a helpful AI assistant for processing sample requests."
            user_prompt = context.sample_prompt
            
            # Call LLM provider
            response = await self._llm_provider.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                chat_id=context.chat_id
            )
            
            # Validate response schema if enabled
            if context.validate_schema:
                self._validate_response_schema(response)
            
            # Log telemetry
            if self._telemetry_service and hasattr(self._telemetry_service, "log_event"):
                self._telemetry_service.log_event("AIProcessingCompleted", {
                    "ChatId": context.chat_id,
                    "PromptLength": str(len(context.sample_prompt)),
                    "ResponseLength": str(len(response.content))
                })
            
            return AISampleCommandResult(
                ai_response=response.content,
                model_used=response.model,
                tokens_used=response.usage.get("total_tokens")
            )
            
        except Exception as e:
            if self._telemetry_service and hasattr(self._telemetry_service, "log_error"):
                self._telemetry_service.log_error(
                    f"AI processing failed: {str(e)}",
                    {"Error": str(e), "ChatId": context.chat_id}
                )
            raise CommandException(f"AI processing failed: {str(e)}") from e
    
    async def _process_without_ai(self, sample_prompt: str) -> AISampleCommandResult:
        """Process without AI (fallback)."""
        # Simple fallback logic
        response = f"Fallback response for: {sample_prompt}"
        
        return AISampleCommandResult(
            ai_response=response,
            model_used="fallback",
            tokens_used=0
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