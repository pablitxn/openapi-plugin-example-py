"""Plugin options for the example plugin."""
from typing import Dict, Optional

from openapi_plugin_common import PluginOptionsBase
from pydantic import BaseModel, Field


class PromptsConfig(BaseModel):
    """Configuration for prompts."""
    
    system_prompt: str = Field(
        ...,
        description="System prompt for AI completion"
    )
    user_prompt: str = Field(
        ...,
        description="User prompt template with placeholders"
    )


class SchemasConfig(BaseModel):
    """Configuration for JSON schemas."""
    
    sample: str = Field(
        ...,
        description="JSON schema for sample response validation"
    )
    ai_sample: str = Field(
        ...,
        description="JSON schema for AI sample response validation"
    )


class CacheConfig(BaseModel):
    """Configuration for caching."""
    
    enabled: bool = Field(default=True, description="Whether caching is enabled")
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    ttl_seconds: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI integration."""
    
    api_key: str = Field(..., description="OpenAI API key")
    model: str = Field(default="gpt-4", description="Model to use")
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for generation"
    )
    max_tokens: int = Field(
        default=1000,
        gt=0,
        description="Maximum tokens to generate"
    )


class ExamplePluginOptions(PluginOptionsBase):
    """Options for the example plugin."""
    
    # Prompts configuration
    prompts: Dict[str, PromptsConfig] = Field(
        default_factory=dict,
        description="Prompts configuration by name"
    )
    
    # Schemas configuration
    schemas: SchemasConfig = Field(
        ...,
        description="JSON schemas for response validation"
    )
    
    # Cache configuration
    cache: CacheConfig = Field(
        default_factory=CacheConfig,
        description="Cache configuration"
    )
    
    # OpenAI configuration
    openai: Optional[OpenAIConfig] = Field(
        default=None,
        description="OpenAI configuration"
    )
    
    # Additional plugin-specific settings
    max_file_size_mb: int = Field(
        default=10,
        gt=0,
        description="Maximum file size in MB"
    )
    
    processing_timeout_seconds: int = Field(
        default=30,
        gt=0,
        description="Processing timeout in seconds"
    )
    
    supported_file_types: list[str] = Field(
        default=["pdf", "txt", "docx", "json"],
        description="Supported file types for processing"
    )