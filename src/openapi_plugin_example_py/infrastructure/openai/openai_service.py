"""OpenAI service implementation."""
import json
from typing import Any, Dict, Optional

from openai import AsyncOpenAI


class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        telemetry_service: Optional[object] = None
    ):
        """Initialize OpenAI service."""
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.telemetry_service = telemetry_service
    
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        chat_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None
    ) -> Dict[str, Any]:
        """Generate a completion using OpenAI."""
        try:
            # Build messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Use provided values or defaults
            temp = temperature if temperature is not None else self.temperature
            max_tok = max_tokens if max_tokens is not None else self.max_tokens
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                response_format=response_format
            )
            
            # Log telemetry
            if self.telemetry_service and hasattr(self.telemetry_service, "log_event"):
                self.telemetry_service.log_event("OpenAICompletionGenerated", {
                    "Model": self.model,
                    "ChatId": chat_id or "",
                    "PromptTokens": str(response.usage.prompt_tokens),
                    "CompletionTokens": str(response.usage.completion_tokens),
                    "TotalTokens": str(response.usage.total_tokens)
                })
            
            # Return structured response
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            if self.telemetry_service and hasattr(self.telemetry_service, "log_error"):
                self.telemetry_service.log_error(
                    f"OpenAI completion failed: {str(e)}",
                    {"Error": str(e), "Model": self.model, "ChatId": chat_id or ""}
                )
            raise
    
    async def generate_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: str,
        chat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured output validated against a JSON schema."""
        # Request JSON response format
        response = await self.generate_completion(
            system_prompt=system_prompt + "\n\nRespond with valid JSON only.",
            user_prompt=user_prompt,
            chat_id=chat_id,
            response_format={"type": "json_object"}
        )
        
        # Parse and validate response
        try:
            result = json.loads(response["content"])
            
            # TODO: Add JSON schema validation here
            # For now, just return the parsed JSON
            
            return result
            
        except json.JSONDecodeError as e:
            if self.telemetry_service and hasattr(self.telemetry_service, "log_error"):
                self.telemetry_service.log_error(
                    f"Failed to parse OpenAI JSON response: {str(e)}",
                    {"Error": str(e), "ChatId": chat_id or "", "Response": response["content"]}
                )
            raise ValueError(f"Invalid JSON response from OpenAI: {str(e)}")