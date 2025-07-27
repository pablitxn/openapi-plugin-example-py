"""Telemetry middleware for HTTP requests."""
from openapi_plugin_common.middleware import (
    TelemetryMiddleware as BaseTelemetryMiddleware,
    TelemetryConfig
)

# Re-export the common telemetry middleware with custom configuration
class TelemetryMiddleware(BaseTelemetryMiddleware):
    """Middleware for logging HTTP requests and responses with telemetry."""
    
    def __init__(self, app):
        """Initialize with custom configuration for the example plugin."""
        config = TelemetryConfig(
            service_name="openapi-plugin-example",
            # Include custom headers relevant to this plugin
            include_headers=[
                "x-correlation-id", 
                "x-chat-id", 
                "x-agent-id",
                "x-request-id",
                "user-agent",
                "x-user-id",
                "x-session-id"
            ],
            # Exclude health check and documentation endpoints
            exclude_paths={
                "/health", "/healthz", "/ready", "/readyz",
                "/docs", "/redoc", "/openapi.json", "/favicon.ico",
                "/.well-known/ai-plugin.json"
            },
            # Log slow requests over 1 second
            slow_request_threshold_ms=1000.0
        )
        super().__init__(app, config=config)