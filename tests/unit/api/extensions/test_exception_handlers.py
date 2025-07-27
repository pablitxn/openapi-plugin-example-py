"""Unit tests for exception handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

from src.openapi_plugin_example_py.api.extensions.exception_handlers import (
    configure_exception_handlers
)


class TestExceptionHandlers:
    """Test suite for exception handlers."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        app = FastAPI()
        app.state = MagicMock()
        app.exception_handlers = {}
        
        # Mock the exception_handler decorator
        def exception_handler(exception_class):
            def decorator(func):
                app.exception_handlers[exception_class] = func
                return func
            return decorator
        
        app.exception_handler = exception_handler
        return app

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = MagicMock(spec=Request)
        request.url = "http://test.com/api/test"
        return request

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.environment = "development"
        return settings

    def test_configure_exception_handlers(self, mock_app):
        """Test that exception handlers are configured."""
        # Act
        configure_exception_handlers(mock_app)
        
        # Assert
        assert Exception in mock_app.exception_handlers
        assert callable(mock_app.exception_handlers[Exception])

    @pytest.mark.asyncio
    async def test_global_exception_handler_development(self, mock_app, mock_request, mock_settings):
        """Test global exception handler in development environment."""
        # Arrange
        configure_exception_handlers(mock_app)
        handler = mock_app.exception_handlers[Exception]
        
        test_exception = ValueError("Test error message")
        mock_app.state.logger = MagicMock()
        
        # Set up request headers
        mock_request.headers = {
            "x-correlation-id": "test-correlation-id",
            "x-user-id": "test-user"
        }
        mock_request.method = "POST"
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            # Act
            response = await handler(mock_request, test_exception)
            
            # Assert
            assert isinstance(response, JSONResponse)
            assert response.status_code == 500
            
            # Verify response content in development mode
            import json
            content = json.loads(response.body)
            assert content["type"] == "https://tools.ietf.org/html/rfc7231#section-6.6.1"
            assert content["title"] == "Internal Server Error"
            assert content["status"] == 500
            assert content["detail"] == "Test error message"  # Full error in development
            assert content["instance"] == "http://test.com/api/test"
            assert "stackTrace" in content  # Stack trace in development
            
            # Verify logging
            mock_app.state.logger.error.assert_called_once()
            
            # Verify response headers
            assert response.headers.get("X-Correlation-Id") == "test-correlation-id"

    @pytest.mark.asyncio
    async def test_global_exception_handler_production(self, mock_app, mock_request):
        """Test global exception handler in production environment."""
        # Arrange
        configure_exception_handlers(mock_app)
        handler = mock_app.exception_handlers[Exception]
        
        test_exception = RuntimeError("Sensitive error details")
        mock_app.state.logger = None  # No logger
        
        mock_settings = MagicMock()
        mock_settings.environment = "production"
        
        # Set up request with no headers
        mock_request.headers = {}
        mock_request.method = "GET"
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.BaseLogger') as mock_base_logger:
                mock_logger_instance = MagicMock()
                mock_base_logger.return_value = mock_logger_instance
                
                # Act
                response = await handler(mock_request, test_exception)
                
                # Assert
                assert response.status_code == 500
                
                # Verify response content in production mode
                import json
                content = json.loads(response.body)
                assert content["type"] == "https://tools.ietf.org/html/rfc7231#section-6.6.1"
                assert content["title"] == "Internal Server Error"
                assert content["status"] == 500
                assert content["detail"] == "An error occurred while processing your request."  # Generic message in production
                assert content["instance"] == "http://test.com/api/test"
                assert "stackTrace" not in content  # No stack trace in production
                
                # Verify logger was created
                mock_base_logger.assert_called_once()
                mock_logger_instance.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_global_exception_handler_no_telemetry(self, mock_request, mock_settings):
        """Test global exception handler when telemetry service is not available."""
        # Arrange
        # Create app without telemetry_service attribute
        app = FastAPI()
        app.state = MagicMock(spec=[])  # Empty spec means no attributes
        app.exception_handlers = {}
        
        def exception_handler(exception_class):
            def decorator(func):
                app.exception_handlers[exception_class] = func
                return func
            return decorator
        
        app.exception_handler = exception_handler
        
        configure_exception_handlers(app)
        handler = app.exception_handlers[Exception]
        
        test_exception = Exception("Test exception")
        
        # Update request 
        mock_request.app = app
        mock_request.headers = {}
        mock_request.method = "GET"
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.BaseLogger') as mock_base_logger:
                mock_logger_instance = MagicMock()
                mock_base_logger.return_value = mock_logger_instance
                
                # Act
                response = await handler(mock_request, test_exception)
                
                # Assert
                assert response.status_code == 500
                # BaseLogger should be instantiated when no logger exists
                mock_base_logger.assert_called_once()
                mock_logger_instance.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_global_exception_handler_with_telemetry_none(self, mock_app, mock_request, mock_settings):
        """Test global exception handler when telemetry service exists but is None."""
        # Arrange
        configure_exception_handlers(mock_app)
        handler = mock_app.exception_handlers[Exception]
        
        test_exception = Exception("Test exception")
        mock_app.state.telemetry_service = None  # Explicitly None
        mock_app.state.logger = MagicMock()  # Existing logger
        
        mock_request.headers = {}
        mock_request.method = "GET"
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            # Act
            response = await handler(mock_request, test_exception)
            
            # Assert
            assert response.status_code == 500
            # Should use existing logger
            mock_app.state.logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_global_exception_handler_response_content(self, mock_app, mock_request, mock_settings):
        """Test that the response contains the expected problem details."""
        # Arrange
        configure_exception_handlers(mock_app)
        handler = mock_app.exception_handlers[Exception]
        
        test_exception = Exception("Test exception")
        mock_app.state.logger = MagicMock()
        
        mock_request.headers = {}
        mock_request.method = "GET"
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            # Act
            response = await handler(mock_request, test_exception)
            
            # Assert
            assert response.status_code == 500
            # JSONResponse content would be the expected_content
            assert response.body  # Response has content
            
            import json
            content = json.loads(response.body)
            assert content["type"] == "https://tools.ietf.org/html/rfc7231#section-6.6.1"
            assert content["title"] == "Internal Server Error"
            assert content["status"] == 500
            assert content["instance"] == "http://test.com/api/test"
    
    @pytest.mark.asyncio
    async def test_global_exception_handler_with_correlation_id(self, mock_app, mock_request, mock_settings):
        """Test that correlation ID is included in response headers."""
        # Arrange
        configure_exception_handlers(mock_app)
        handler = mock_app.exception_handlers[Exception]
        
        test_exception = Exception("Test exception")
        mock_app.state.logger = MagicMock()
        
        # Set up request with correlation ID
        mock_request.headers = {"x-correlation-id": "test-correlation-123"}
        mock_request.method = "GET"
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            # Act
            response = await handler(mock_request, test_exception)
            
            # Assert
            assert response.status_code == 500
            assert response.headers.get("X-Correlation-Id") == "test-correlation-123"
    
    @pytest.mark.asyncio
    async def test_global_exception_handler_creates_logger(self, mock_app, mock_request, mock_settings):
        """Test that a logger is created when app.state.logger is not available."""
        # Arrange
        configure_exception_handlers(mock_app)
        handler = mock_app.exception_handlers[Exception]
        
        test_exception = Exception("Test exception")
        mock_app.state.logger = None  # No logger
        
        mock_request.headers = {}
        mock_request.method = "GET"
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.BaseLogger') as mock_base_logger:
                with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.LoggerConfig') as mock_logger_config:
                    mock_logger_instance = MagicMock()
                    mock_base_logger.return_value = mock_logger_instance
                    
                    # Act
                    response = await handler(mock_request, test_exception)
                    
                    # Assert
                    assert response.status_code == 500
                    # Verify logger was created
                    mock_logger_config.assert_called_once_with(name="exception_handler")
                    mock_base_logger.assert_called_once_with(
                        mock_logger_config.return_value,
                        None  # No telemetry service parameter in the implementation
                    )
                    mock_logger_instance.error.assert_called_once()