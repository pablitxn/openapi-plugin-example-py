"""Unit tests for telemetry middleware."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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
    def middleware(self):
        """Create telemetry middleware instance."""
        return TelemetryMiddleware(app=None)

    @pytest.mark.asyncio
    async def test_dispatch_with_telemetry_service(self, middleware, mock_request):
        """Test dispatch with telemetry service available."""
        # Arrange
        mock_response = Response(content="OK", status_code=200)
        
        async def mock_call_next(request):
            return mock_response
        
        mock_uuid = MagicMock()
        mock_uuid.__str__.return_value = 'test-uuid'
        with patch('uuid.uuid4', return_value=mock_uuid):
            # Act
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert response.status_code == 200
            assert response.headers["X-Correlation-Id"] == "test-uuid"
            
            # Verify telemetry logging
            telemetry_service = mock_request.app.state.telemetry_service
            
            # Check request start event
            assert telemetry_service.log_event.call_count == 2
            first_call = telemetry_service.log_event.call_args_list[0]
            assert first_call[0][0] == "HttpRequestStarted"
            assert first_call[0][1]["Method"] == "GET"
            assert first_call[0][1]["Path"] == "/test"
            assert first_call[0][1]["UserAgent"] == "TestAgent/1.0"
            assert first_call[0][1]["ChatId"] == "chat-123"
            assert first_call[0][1]["AgentId"] == "agent-456"
            assert first_call[0][1]["CorrelationId"] == "test-uuid"
            
            # Check request completed event (properties should include status and elapsed time)
            completed_calls = [call for call in telemetry_service.log_event.call_args_list
                             if call[0][0] == "HttpRequestCompleted"]
            assert len(completed_calls) == 1
            completed_properties = completed_calls[0][0][1]
            assert completed_properties["StatusCode"] == "200"
            assert "ElapsedMilliseconds" in completed_properties

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
        
        # Act
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert response.headers["X-Correlation-Id"] == "existing-correlation-id"
        
        # Verify correlation ID was used in telemetry
        telemetry_service = mock_request.app.state.telemetry_service
        start_call = telemetry_service.log_event.call_args_list[0]
        assert start_call[0][1]["CorrelationId"] == "existing-correlation-id"

    @pytest.mark.asyncio
    async def test_dispatch_with_error_response(self, middleware, mock_request):
        """Test dispatch with error response (4xx/5xx)."""
        # Arrange
        mock_response = Response(content="Not Found", status_code=404)
        
        async def mock_call_next(request):
            return mock_response
        
        # Act
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert response.status_code == 404
        
        # Verify warning was logged for error response
        telemetry_service = mock_request.app.state.telemetry_service
        telemetry_service.log_warning.assert_called_once()
        warning_call = telemetry_service.log_warning.call_args
        assert "HTTP 404 for GET /test" in warning_call[0][0]

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
        
        # Act
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Assert - should work without errors
        assert response.status_code == 200
        assert "X-Correlation-Id" in response.headers

    @pytest.mark.asyncio
    async def test_dispatch_timing(self, middleware, mock_request):
        """Test that elapsed time is calculated correctly."""
        # Arrange
        mock_response = Response(content="OK", status_code=200)
        call_delay = 0.1  # 100ms delay
        
        async def mock_call_next(request):
            await AsyncMock()()  # Simulate some async work
            time.sleep(call_delay)  # Add a delay
            return mock_response
        
        # Act
        start = time.time()
        response = await middleware.dispatch(mock_request, mock_call_next)
        end = time.time()
        
        # Assert
        actual_elapsed = (end - start) * 1000
        
        # Check that elapsed time was logged
        telemetry_service = mock_request.app.state.telemetry_service
        completed_calls = [call for call in telemetry_service.log_event.call_args_list
                         if call[0][0] == "HttpRequestCompleted"]
        
        logged_elapsed = float(completed_calls[0][0][1]["ElapsedMilliseconds"])
        
        # Elapsed time should be at least the delay we added
        assert logged_elapsed >= call_delay * 1000
        # And reasonably close to actual elapsed time (within 50ms tolerance)
        assert abs(logged_elapsed - actual_elapsed) < 50

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
        
        # Act
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        telemetry_service = mock_app.state.telemetry_service
        start_call = telemetry_service.log_event.call_args_list[0]
        properties = start_call[0][1]
        
        # Verify empty values for missing headers
        assert properties["UserAgent"] == ""
        assert properties["ChatId"] == ""
        assert properties["AgentId"] == ""

    @pytest.mark.asyncio
    async def test_dispatch_with_server_error(self, middleware, mock_request):
        """Test dispatch with 5xx server error."""
        # Arrange
        mock_response = Response(content="Internal Server Error", status_code=500)
        
        async def mock_call_next(request):
            return mock_response
        
        # Act
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert response.status_code == 500
        
        # Verify warning was logged for server error
        telemetry_service = mock_request.app.state.telemetry_service
        telemetry_service.log_warning.assert_called_once()
        warning_call = telemetry_service.log_warning.call_args
        assert "HTTP 500 for GET /test" in warning_call[0][0]
        assert warning_call[0][1]["StatusCode"] == "500"

    @pytest.mark.asyncio
    async def test_dispatch_no_telemetry_attribute(self, middleware):
        """Test dispatch when app.state has no telemetry_service attribute."""
        # Arrange
        mock_app = MagicMock()
        mock_app.state = MagicMock(spec=[])  # Empty spec, no attributes
        
        mock_request = MagicMock(spec=Request)
        mock_request.app = mock_app
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.headers = {}
        
        mock_response = Response(content="OK", status_code=200)
        
        async def mock_call_next(request):
            return mock_response
        
        # Act
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Assert - should work without errors
        assert response.status_code == 200
        assert "X-Correlation-Id" in response.headers