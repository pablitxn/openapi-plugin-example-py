"""Application settings configuration."""
import json
from typing import Any, Dict, Optional

from openapi_plugin_common import (
    BlobStorageSettings,
    TelemetrySettings,
)
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..business_logic.options import ExamplePluginOptions


class SecuritySettings(BaseSettings):
    """Security settings for the application."""
    
    client_id: str = Field(..., description="Application client ID")
    tenant_id: str = Field(
        default="5b973f99-77df-4beb-b27d-aa0c70b8482c",
        description="Azure AD tenant ID"
    )
    api_audience: str = Field(..., description="API audience for JWT validation")
    client_secret: Optional[str] = Field(
        default=None,
        description="Client secret for authentication"
    )
    geney_client_id: Optional[str] = Field(
        default=None,
        description="GenEY client ID for API access"
    )
    geney_api_domain: Optional[str] = Field(
        default=None,
        description="GenEY API domain"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        case_sensitive=False
    )


class AppSettings(BaseSettings):
    """Main application settings."""
    
    # Environment
    environment: str = Field(
        default="development",
        description="Application environment"
    )
    
    # API settings
    api_prefix: str = Field(
        default="/api/plugin/ExamplePlugin",
        description="API route prefix"
    )
    api_version: str = Field(
        default="v1",
        description="API version"
    )
    
    # Security - flattened to allow env loading
    security_client_id: str = Field(..., description="Application client ID")
    security_tenant_id: str = Field(
        default="5b973f99-77df-4beb-b27d-aa0c70b8482c",
        description="Azure AD tenant ID"
    )
    security_api_audience: str = Field(..., description="API audience for JWT validation")
    security_client_secret: Optional[str] = Field(
        default=None,
        description="Client secret for authentication"
    )
    security_geney_client_id: Optional[str] = Field(
        default=None,
        description="GenEY client ID for API access"
    )
    security_geney_api_domain: Optional[str] = Field(
        default=None,
        description="GenEY API domain"
    )
    
    @property
    def security(self) -> SecuritySettings:
        """Get security settings."""
        return SecuritySettings(
            client_id=self.security_client_id,
            tenant_id=self.security_tenant_id,
            api_audience=self.security_api_audience,
            client_secret=self.security_client_secret,
            geney_client_id=self.security_geney_client_id,
            geney_api_domain=self.security_geney_api_domain
        )
    
    # Telemetry
    telemetry: TelemetrySettings = Field(
        default_factory=TelemetrySettings,
        description="Telemetry settings"
    )
    
    # Blob storage
    blob_storage: Optional[BlobStorageSettings] = Field(
        default=None,
        description="Blob storage settings"
    )
    
    # Plugin options
    plugin_options: ExamplePluginOptions = Field(
        default_factory=ExamplePluginOptions,
        description="Plugin-specific options"
    )
    
    # Redis cache
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL"
    )
    
    # CORS
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )
    
    @field_validator("plugin_options", mode="before")
    def parse_plugin_options(cls, v):
        """Parse plugin options from JSON string if needed."""
        if isinstance(v, str):
            return json.loads(v)
        return v


def get_settings() -> AppSettings:
    """Get application settings."""
    return AppSettings()