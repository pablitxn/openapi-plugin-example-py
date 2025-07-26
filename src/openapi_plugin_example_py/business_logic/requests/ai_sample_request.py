"""AI sample request models."""
from typing import Optional

from openapi_plugin_common import RequestBase
from pydantic import BaseModel, Field


class AISampleRequest(RequestBase):
    """Request model for AI sample endpoint."""
    
    sample_prompt: str = Field(
        ...,
        description="The prompt to send to the AI model",
        example="Explain quantum computing in simple terms",
        min_length=1,
        max_length=2000
    )
    use_ai: bool = Field(
        default=True,
        description="Whether to use AI for processing (fallback to simple processing if false)"
    )
    validate_schema: bool = Field(
        default=True,
        description="Whether to validate the AI response against the schema"
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Override temperature for AI generation"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        le=4000,
        description="Override max tokens for AI generation"
    )


class AISampleResponse(BaseModel):
    """Response model for AI sample endpoint."""
    
    ai_response: str = Field(
        ...,
        description="The AI-generated response"
    )
    model_used: Optional[str] = Field(
        default=None,
        description="The AI model that was used"
    )
    tokens_used: Optional[int] = Field(
        default=None,
        description="Number of tokens consumed"
    )
    cached: bool = Field(
        default=False,
        description="Whether the response was served from cache"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "ai_response": "Quantum computing is a type of computing that uses quantum mechanics...",
                "model_used": "gpt-4",
                "tokens_used": 150,
                "cached": False
            }
        }