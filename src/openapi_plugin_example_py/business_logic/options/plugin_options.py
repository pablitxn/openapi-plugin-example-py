"""Plugin options for the example plugin."""
from typing import Dict, Optional

from openapi_plugin_common import (
    CacheConfig,
    OpenAIConfig,
    PluginOptionsBase,
    PromptsConfig,
    SchemasConfig,
)
from pydantic import Field


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