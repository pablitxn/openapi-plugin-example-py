"""Mock authentication for development/testing purposes."""
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


class MockJWTBearer(HTTPBearer):
    """Mock JWT Bearer authentication for development.
    
    This bypasses real authentication and returns a mock user.
    """
    
    def __init__(self, auto_error: bool = True):
        """Initialize mock JWT Bearer."""
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Dict[str, Any]:
        """Return mock authentication data."""
        # Check if Authorization header exists (for compatibility)
        credentials = await super().__call__(request)
        
        # Return mock user data
        return {
            "sub": "mock-user-123",
            "name": "Mock User",
            "email": "mock@example.com",
            "chat_id": request.headers.get("x-chat-id", "mock-chat-123"),
            "agent_id": request.headers.get("x-agent-id", "mock-agent-456"),
            "tenant_id": "5b973f99-77df-4beb-b27d-aa0c70b8482c",
            "roles": ["user", "admin"]
        }


def mock_requires_auth(f):
    """Mock decorator for functions that require authentication.
    
    This decorator bypasses authentication for development.
    """
    def wrapper(*args, **kwargs):
        # Inject mock token if needed
        if "token" in kwargs:
            kwargs["token"] = "mock-token-123"
        return f(*args, **kwargs)
    return wrapper


def mock_requires_scope(scope: str):
    """Mock decorator for scope validation.
    
    Always returns True in development mode.
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator