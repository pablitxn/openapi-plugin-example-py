"""AI sample request models."""
from typing import List, Literal, Optional, Union

from openapi_plugin_common import RequestBase
from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """Chat message in OpenAI format."""
    
    role: Literal["system", "user", "assistant"] = Field(
        ...,
        description="The role of the message author"
    )
    content: str = Field(
        ...,
        description="The content of the message"
    )
    name: Optional[str] = Field(
        default=None,
        description="Optional name of the message author"
    )


class AISampleRequest(RequestBase):
    """Request model for AI sample endpoint in OpenAI chat completion format."""
    
    messages: List[ChatMessage] = Field(
        ...,
        description="List of messages in the conversation",
        min_length=1,
        json_schema_extra={
            "example": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Explain quantum computing in simple terms"}
            ]
        }
    )
    model: Optional[str] = Field(
        default=None,
        description="ID of the model to use. If not specified, uses the default from config"
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Sampling temperature between 0 and 2"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        le=4000,
        description="Maximum number of tokens to generate"
    )
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    n: Optional[int] = Field(
        default=1,
        ge=1,
        le=1,
        description="Number of completions to generate (currently only 1 is supported)"
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Whether to stream the response (not yet implemented)"
    )
    stop: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Sequences where the API will stop generating"
    )
    presence_penalty: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=2.0,
        description="Presence penalty for frequency of new tokens"
    )
    frequency_penalty: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty for repeated tokens"
    )
    user: Optional[str] = Field(
        default=None,
        description="Unique identifier for the end-user"
    )


class ChatChoice(BaseModel):
    """Chat completion choice."""
    
    index: int = Field(
        ...,
        description="The index of this choice"
    )
    message: ChatMessage = Field(
        ...,
        description="The generated message"
    )
    finish_reason: Optional[Literal["stop", "length", "content_filter", "null"]] = Field(
        default="stop",
        description="Reason the generation stopped"
    )


class Usage(BaseModel):
    """Token usage information."""
    
    prompt_tokens: int = Field(
        ...,
        description="Number of tokens in the prompt"
    )
    completion_tokens: int = Field(
        ...,
        description="Number of tokens in the completion"
    )
    total_tokens: int = Field(
        ...,
        description="Total number of tokens used"
    )


class AISampleResponse(BaseModel):
    """Response model for AI sample endpoint in OpenAI chat completion format."""
    
    id: str = Field(
        ...,
        description="Unique identifier for the chat completion"
    )
    object: Literal["chat.completion"] = Field(
        default="chat.completion",
        description="Object type"
    )
    created: int = Field(
        ...,
        description="Unix timestamp of when the completion was created"
    )
    model: str = Field(
        ...,
        description="Model used for the completion"
    )
    choices: List[ChatChoice] = Field(
        ...,
        description="List of completion choices"
    )
    usage: Usage = Field(
        ...,
        description="Token usage statistics"
    )
    system_fingerprint: Optional[str] = Field(
        default=None,
        description="System fingerprint for the model configuration"
    )
    cached: bool = Field(
        default=False,
        description="Whether the response was served from cache (custom field)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1677652288,
                "model": "gpt-4o-mini",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Quantum computing is a revolutionary approach to computation..."
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 25,
                    "completion_tokens": 125,
                    "total_tokens": 150
                },
                "cached": False
            }
        }
    )