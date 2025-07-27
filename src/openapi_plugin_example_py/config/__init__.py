"""Configuration module for the example plugin."""
from openapi_plugin_common import SecuritySettings

from .settings import AppSettings, get_settings

__all__ = [
    "AppSettings",
    "SecuritySettings",
    "get_settings",
]