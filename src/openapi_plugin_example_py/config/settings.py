"""Application settings configuration."""
import json

from openapi_plugin_common import (
    BaseAppSettings,
    get_settings as get_base_settings,
)
from pydantic import Field, field_validator

from ..business_logic.options import ExamplePluginOptions


class AppSettings(BaseAppSettings):
    """Application settings for the Example Plugin."""
    
    # Override default API prefix for this plugin
    api_prefix: str = Field(
        default="/api/plugin/ExamplePlugin",
        description="API route prefix"
    )
    
    # Plugin options
    plugin_options: ExamplePluginOptions = Field(
        default_factory=ExamplePluginOptions,
        description="Plugin-specific options"
    )
    
    @field_validator("plugin_options", mode="before")
    def parse_plugin_options(cls, v):
        """Parse plugin options from JSON string if needed."""
        if isinstance(v, str):
            return json.loads(v)
        return v


def get_settings() -> AppSettings:
    """Get application settings."""
    return get_base_settings(AppSettings)