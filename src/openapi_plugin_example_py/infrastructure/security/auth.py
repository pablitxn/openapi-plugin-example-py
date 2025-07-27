"""Authentication configuration for the Example Plugin.

This module provides authentication setup using the common security components.
For compatibility with the GenEY guide, it also includes the @requires_auth decorator.
"""
from functools import wraps
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from openapi_plugin_common import JWTBearer as CommonJWTBearer, requires_auth as common_requires_auth

from ...config import get_settings


class JWTBearer(CommonJWTBearer):
    """JWT Bearer authentication for Example Plugin.
    
    This class extends the common JWTBearer with plugin-specific configuration.
    """
    
    def __init__(self, api_audience: Optional[str] = None, bypass_auth: Optional[bool] = None):
        """Initialize JWT Bearer with plugin settings."""
        settings = get_settings()
        self.bypass_auth = bypass_auth if bypass_auth is not None else settings.bypass_auth
        
        if not self.bypass_auth:
            super().__init__(
                tenant_id=settings.security.tenant_id,
                api_audience=api_audience or settings.security.api_audience
            )
    
    async def __call__(self, request: Request) -> Dict[str, Any]:
        """Handle authentication based on bypass setting."""
        if self.bypass_auth:
            # Return mock user data in bypass mode
            return {
                "sub": "mock-user-123",
                "name": "Mock User",
                "email": "mock@example.com",
                "chat_id": request.headers.get("x-chat-id", "mock-chat-123"),
                "agent_id": request.headers.get("x-agent-id", "mock-agent-456"),
                "tenant_id": "5b973f99-77df-4beb-b27d-aa0c70b8482c",
                "roles": ["user", "admin"]
            }
        else:
            # Use real authentication
            return await super().__call__(request)


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
    
    if settings.bypass_auth:
        # Return mock decorator in bypass mode
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Inject mock token if needed
            if "token" in kwargs:
                kwargs["token"] = "mock-token-123"
            return f(*args, **kwargs)
        return wrapper
    else:
        # Use real authentication
        return common_requires_auth(
            tenant_id=settings.security.tenant_id,
            api_audience=settings.security.api_audience
        )(f)


# Re-export common security utilities
from openapi_plugin_common import requires_scope, AuthError  # noqa: E402