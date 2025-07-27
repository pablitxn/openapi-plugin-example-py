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
    
    # Development/Testing bypass settings
    bypass_auth: bool = Field(
        default=False,
        description="Bypass authentication for development"
    )
    use_filesystem_storage: bool = Field(
        default=False,
        description="Use filesystem instead of Azure Blob Storage"
    )
    filesystem_storage_path: str = Field(
        default="./mock_storage",
        description="Path for filesystem storage"
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
    import os
    from .json_loader import load_json_config
    
    # Load configuration from JSON files
    environment = os.getenv("ENVIRONMENT", "development")
    json_config = load_json_config(environment.capitalize())
    
    # Set complex objects as JSON strings for pydantic-settings
    if "plugin_options" in json_config:
        os.environ["PLUGIN_OPTIONS"] = json.dumps(json_config["plugin_options"])
    
    # Set other simple values
    for key in ["environment", "api_prefix", "api_version", "bypass_auth", "use_filesystem_storage", "filesystem_storage_path"]:
        if key in json_config:
            os.environ[key.upper()] = str(json_config[key])
    
    # Set security values
    if "security" in json_config:
        for k, v in json_config["security"].items():
            os.environ[f"SECURITY_{k.upper()}"] = str(v)
    
    # Set telemetry
    if "telemetry" in json_config:
        os.environ["TELEMETRY"] = json.dumps(json_config["telemetry"])
    
    # Set blob storage
    if "blob_storage" in json_config:
        os.environ["BLOB_STORAGE"] = json.dumps(json_config["blob_storage"])
    
    # Set redis url
    if "redis_url" in json_config:
        os.environ["REDIS_URL"] = json_config["redis_url"]
    
    # Set CORS origins
    if "cors_origins" in json_config:
        os.environ["CORS_ORIGINS"] = json.dumps(json_config["cors_origins"])
    
    return AppSettings()