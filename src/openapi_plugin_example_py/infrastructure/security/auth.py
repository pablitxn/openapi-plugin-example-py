"""Authentication configuration for the Example Plugin.

This module provides authentication setup using the common security components.
For compatibility with the GenEY guide, it also includes the @requires_auth decorator.
"""
from functools import wraps
from typing import Optional

from fastapi import Depends, HTTPException, Request
from openapi_plugin_common import JWTBearer as CommonJWTBearer, requires_auth as common_requires_auth

from ...config import get_settings


class JWTBearer(CommonJWTBearer):
    """JWT Bearer authentication for Example Plugin.
    
    This class extends the common JWTBearer with plugin-specific configuration.
    """
    
    def __init__(self, api_audience: Optional[str] = None):
        """Initialize JWT Bearer with plugin settings."""
        settings = get_settings()
        super().__init__(
            tenant_id=settings.security.tenant_id,
            api_audience=api_audience or settings.security.api_audience
        )


def requires_auth(f):
    """Decorator for functions that require authentication.
    
    This decorator provides compatibility with the GenEY design guide.
    For FastAPI endpoints, use Depends(JWTBearer) instead.
    
    Example:
        @requires_auth
        async def my_function(token: str, ...):
            # Function implementation
    """
    settings = get_settings()
    return common_requires_auth(
        tenant_id=settings.security.tenant_id,
        api_audience=settings.security.api_audience
    )(f)


# Re-export common security utilities
from openapi_plugin_common import requires_scope  # noqa: E402