"""JWT authentication implementation following Azure AD standards."""
import json
from functools import wraps
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from six.moves.urllib.request import urlopen

# Fixed Azure AD tenant ID as per requirements
TENANT_ID = "5b973f99-77df-4beb-b27d-aa0c70b8482c"


class AuthError(Exception):
    """Authentication error."""
    
    def __init__(self, error: dict, status_code: int):
        """Initialize auth error."""
        self.error = error
        self.status_code = status_code


class JWTBearer(HTTPBearer):
    """JWT Bearer authentication."""
    
    def __init__(self, api_audience: str, auto_error: bool = True):
        """Initialize JWT Bearer."""
        super().__init__(auto_error=auto_error)
        self.api_audience = api_audience
        self._jwks_cache = None
        self._jwks_cache_time = 0
    
    async def __call__(self, request: Request) -> Optional[str]:
        """Validate JWT token."""
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=401,
                    detail={
                        "code": "invalid_header",
                        "description": "Authorization header must start with Bearer"
                    }
                )
            
            token = credentials.credentials
            
            try:
                payload = await self._verify_token(token)
                request.state.jwt_payload = payload
                return token
            except AuthError as e:
                raise HTTPException(
                    status_code=e.status_code,
                    detail=e.error
                )
        
        return None
    
    async def _verify_token(self, token: str) -> dict:
        """Verify JWT token."""
        # Get JWKS (with caching)
        jwks = await self._get_jwks()
        
        # Get unverified header
        try:
            unverified_header = jwt.get_unverified_header(token)
        except Exception:
            raise AuthError({
                "code": "invalid_header",
                "description": "Unable to parse authentication token."
            }, 401)
        
        # Find RSA key
        rsa_key = None
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            raise AuthError({
                "code": "invalid_header",
                "description": "Unable to find appropriate key"
            }, 401)
        
        # Verify token
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=self.api_audience,
                issuer=f"https://sts.windows.net/{TENANT_ID}/"
            )
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthError({
                "code": "token_expired",
                "description": "Token is expired"
            }, 401)
            
        except jwt.JWTClaimsError:
            raise AuthError({
                "code": "invalid_claims",
                "description": "Incorrect claims, please check the audience and issuer"
            }, 401)
            
        except Exception:
            raise AuthError({
                "code": "invalid_header",
                "description": "Unable to parse authentication token."
            }, 401)
    
    async def _get_jwks(self) -> dict:
        """Get JWKS from Azure AD (with caching)."""
        import time
        
        # Cache for 1 hour
        if self._jwks_cache and (time.time() - self._jwks_cache_time) < 3600:
            return self._jwks_cache
        
        try:
            jsonurl = urlopen(
                f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
            )
            jwks = json.loads(jsonurl.read())
            
            # Update cache
            self._jwks_cache = jwks
            self._jwks_cache_time = time.time()
            
            return jwks
        except Exception as e:
            raise AuthError({
                "code": "jwks_fetch_error",
                "description": f"Unable to fetch JWKS: {str(e)}"
            }, 500)


def requires_auth(f):
    """Decorator for functions that require authentication."""
    @wraps(f)
    async def decorated(*args, **kwargs):
        # This is for non-FastAPI functions
        # For FastAPI, use Depends(JWTBearer) instead
        raise NotImplementedError(
            "Use FastAPI's Depends(JWTBearer) for authentication"
        )
    return decorated


def requires_scope(required_scope: str):
    """Check if the required scope is present in the access token."""
    def decorator(f):
        @wraps(f)
        async def decorated(request: Request, *args, **kwargs):
            # Get JWT payload from request state
            payload = getattr(request.state, "jwt_payload", None)
            if not payload:
                raise HTTPException(
                    status_code=401,
                    detail="No JWT payload found"
                )
            
            # Check scopes
            token_scopes = payload.get("scope", "").split()
            if required_scope not in token_scopes:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "insufficient_scope",
                        "description": f"Required scope '{required_scope}' not found"
                    }
                )
            
            return await f(request, *args, **kwargs)
        return decorated
    return decorator