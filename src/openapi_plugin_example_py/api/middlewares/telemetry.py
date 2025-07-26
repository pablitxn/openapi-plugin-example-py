"""Telemetry middleware for HTTP requests."""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add telemetry."""
        # Generate correlation ID if not present
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        
        # Start timer
        start_time = time.time()
        
        # Get telemetry service from app state
        telemetry_service = getattr(request.app.state, "telemetry_service", None)
        
        # Log request start
        if telemetry_service:
            properties = {
                "Method": request.method,
                "Path": request.url.path,
                "UserAgent": request.headers.get("user-agent", ""),
                "ChatId": request.headers.get("x-chat-id", ""),
                "AgentId": request.headers.get("x-agent-id", ""),
                "CorrelationId": correlation_id
            }
            telemetry_service.log_event("HttpRequestStarted", properties)
        
        # Process request
        response = await call_next(request)
        
        # Calculate elapsed time
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-Id"] = correlation_id
        
        # Log request completion
        if telemetry_service:
            properties["StatusCode"] = str(response.status_code)
            properties["ElapsedMilliseconds"] = str(elapsed_ms)
            
            if response.status_code >= 400:
                telemetry_service.log_warning(
                    f"HTTP {response.status_code} for {request.method} {request.url.path}",
                    properties
                )
            else:
                telemetry_service.log_event("HttpRequestCompleted", properties)
        
        return response