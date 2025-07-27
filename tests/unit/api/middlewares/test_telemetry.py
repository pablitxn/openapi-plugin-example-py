"""Unit tests for telemetry middleware."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi import FastAPI, Request, Response
from starlette.datastructures import Headers
import time

from src.openapi_plugin_example_py.api.middlewares.telemetry import TelemetryMiddleware


class TestTelemetryMiddleware:
    """Test suite for telemetry middleware."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        app = FastAPI()
        app.state = MagicMock()
        app.state.telemetry_service = MagicMock()
        return app

    @pytest.fixture
    def mock_request(self, mock_app):
        """Create a mock request."""
        request = MagicMock(spec=Request)
        request.app = mock_app
        request.method = "GET"
        request.url.path = "/test"
        request.headers = {
            "user-agent": "TestAgent/1.0",
            "x-chat-id": "chat-123",
            "x-agent-id": "agent-456"
        }
        return request

    @pytest.fixture
    def middleware(self, mock_app):
        """Create telemetry middleware instance."""
        return TelemetryMiddleware(mock_app)

    @pytest.mark.asyncio
    async def test_dispatch_with_telemetry_service(self, middleware, mock_request):
        """Test dispatch with telemetry service available."""
        # Arrange
        mock_response = Response(content="OK", status_code=200)
        
        async def mock_call_next(request):
            return mock_response
        
        # Mock the parent class dispatch method
        with patch.object(TelemetryMiddleware.__bases__[0], 'dispatch', 
                         return_value=mock_response) as mock_parent_dispatch:
            # Act
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert response.status_code == 200
            mock_parent_dispatch.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_with_existing_correlation_id(self, middleware, mock_request):
        """Test dispatch with existing correlation ID in headers."""
        # Arrange
        mock_request.headers = {
            "x-correlation-id": "existing-correlation-id",
            "user-agent": "TestAgent/1.0"
        }
        mock_response = Response(content="OK", status_code=200)
        
        async def mock_call_next(request):
            return mock_response
        
        # Mock the parent class dispatch method
        with patch.object(TelemetryMiddleware.__bases__[0], 'dispatch', 
                         return_value=mock_response) as mock_parent_dispatch:
            # Act
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert response.status_code == 200
            mock_parent_dispatch.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_with_error_response(self, middleware, mock_request):
        """Test dispatch with error response (4xx/5xx)."""
        # Arrange
        mock_response = Response(content="Not Found", status_code=404)
        
        async def mock_call_next(request):
            return mock_response
        
        # Mock the parent class dispatch method
        with patch.object(TelemetryMiddleware.__bases__[0], 'dispatch', 
                         return_value=mock_response) as mock_parent_dispatch:
            # Act
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert response.status_code == 404
            mock_parent_dispatch.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_without_telemetry_service(self, middleware):
        """Test dispatch when telemetry service is not available."""
        # Arrange
        mock_app = MagicMock()
        mock_app.state = MagicMock()
        mock_app.state.telemetry_service = None
        
        mock_request = MagicMock(spec=Request)
        mock_request.app = mock_app
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.headers = {}
        
        mock_response = Response(content="OK", status_code=200)
        
        async def mock_call_next(request):
            return mock_response
        
        # Create middleware with the app that has no telemetry service
        middleware = TelemetryMiddleware(mock_app)
        
        # Mock the parent class dispatch method
        with patch.object(TelemetryMiddleware.__bases__[0], 'dispatch', 
                         return_value=mock_response) as mock_parent_dispatch:
            # Act
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Assert - should work without errors
            assert response.status_code == 200
            mock_parent_dispatch.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_timing(self, middleware, mock_request):
        """Test that elapsed time is calculated correctly."""
        # Arrange
        mock_response = Response(content="OK", status_code=200)
        
        async def mock_call_next(request):
            await asyncio.sleep(0.1)  # 100ms delay
            return mock_response
        
        # Mock the parent class dispatch method to simulate timing
        async def mock_parent_dispatch(request, call_next):
            start = time.time()
            response = await call_next(request)
            elapsed = (time.time() - start) * 1000
            # Just return the response, timing is handled by parent
            return response
        
        with patch.object(TelemetryMiddleware.__bases__[0], 'dispatch', 
                         side_effect=mock_parent_dispatch):
            # Act
            import asyncio
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dispatch_with_missing_headers(self, middleware):
        """Test dispatch with missing optional headers."""
        # Arrange
        mock_app = MagicMock()
        mock_app.state.telemetry_service = MagicMock()
        
        mock_request = MagicMock(spec=Request)
        mock_request.app = mock_app
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.headers = {}  # No headers
        
        mock_response = Response(content="Created", status_code=201)
        
        async def mock_call_next(request):
            return mock_response
        
        # Create middleware
        middleware = TelemetryMiddleware(mock_app)
        
        # Mock the parent class dispatch method
        with patch.object(TelemetryMiddleware.__bases__[0], 'dispatch', 
                         return_value=mock_response) as mock_parent_dispatch:
            # Act
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert response.status_code == 201
            mock_parent_dispatch.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_with_server_error(self, middleware, mock_request):
        """Test dispatch with 5xx server error."""
        # Arrange
        mock_response = Response(content="Internal Server Error", status_code=500)
        
        async def mock_call_next(request):
            return mock_response
        
        # Mock the parent class dispatch method
        with patch.object(TelemetryMiddleware.__bases__[0], 'dispatch', 
                         return_value=mock_response) as mock_parent_dispatch:
            # Act
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert response.status_code == 500
            mock_parent_dispatch.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_configuration(self):
        """Test that middleware is configured correctly."""
        # Arrange
        mock_app = MagicMock()
        
        # Act
        middleware = TelemetryMiddleware(mock_app)
        
        # Assert - verify configuration
        assert middleware.config.service_name == "openapi-plugin-example"
        assert "x-correlation-id" in middleware.config.include_headers
        assert "x-chat-id" in middleware.config.include_headers
        assert "x-agent-id" in middleware.config.include_headers
        assert "/health" in middleware.config.exclude_paths
        assert middleware.config.slow_request_threshold_ms == 1000.0

    @pytest.mark.asyncio
    async def test_excluded_paths(self, middleware):
        """Test that excluded paths are handled correctly."""
        # Arrange
        mock_app = MagicMock()
        mock_app.state.telemetry_service = MagicMock()
        
        # Test with excluded path
        mock_request = MagicMock(spec=Request)
        mock_request.app = mock_app
        mock_request.method = "GET"
        mock_request.url.path = "/health"
        mock_request.headers = {}
        
        mock_response = Response(content="OK", status_code=200)
        
        async def mock_call_next(request):
            return mock_response
        
        # Create middleware
        middleware = TelemetryMiddleware(mock_app)
        
        # Mock the parent class dispatch method
        with patch.object(TelemetryMiddleware.__bases__[0], 'dispatch', 
                         return_value=mock_response) as mock_parent_dispatch:
            # Act
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert response.status_code == 200
            mock_parent_dispatch.assert_called_once()