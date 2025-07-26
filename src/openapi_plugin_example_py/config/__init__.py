"""Configuration module for the example plugin."""
from .settings import AppSettings, SecuritySettings, get_settings

__all__ = [
    "AppSettings",
    "SecuritySettings",
    "get_settings",
]