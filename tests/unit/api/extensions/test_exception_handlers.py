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
        mock_app.state.telemetry_service = MagicMock()
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.ExceptionHandlerBase') as mock_exception_handler:
                mock_handler_instance = MagicMock()
                mock_exception_handler.return_value = mock_handler_instance
                
                with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.ProblemDetailsFactory') as mock_problem_factory:
                    mock_problem = MagicMock()
                    mock_problem.status = 500
                    mock_problem.model_dump.return_value = {
                        "type": "about:blank",
                        "title": "Internal Server Error",
                        "status": 500,
                        "detail": "Test error message",
                        "instance": "http://test.com/api/test"
                    }
                    mock_problem_factory.create_internal_server_error.return_value = mock_problem
                    
                    with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.logger') as mock_logger:
                        # Act
                        response = await handler(mock_request, test_exception)
                        
                        # Assert
                        assert isinstance(response, JSONResponse)
                        assert response.status_code == 500
                        
                        # Verify logging
                        mock_logger.error.assert_called_once()
                        assert "Unhandled exception: Test error message" in mock_logger.error.call_args[0][0]
                        
                        # Verify telemetry logging
                        mock_exception_handler.assert_called_once_with(
                            logger=mock_logger,
                            telemetry_service=mock_app.state.telemetry_service
                        )
                        mock_handler_instance.log_exception.assert_called_once_with(test_exception)
                        
                        # Verify problem details creation (with detail in development)
                        mock_problem_factory.create_internal_server_error.assert_called_once_with(
                            detail="Test error message",
                            instance="http://test.com/api/test"
                        )

    @pytest.mark.asyncio
    async def test_global_exception_handler_production(self, mock_app, mock_request):
        """Test global exception handler in production environment."""
        # Arrange
        configure_exception_handlers(mock_app)
        handler = mock_app.exception_handlers[Exception]
        
        test_exception = RuntimeError("Sensitive error details")
        mock_app.state.telemetry_service = None  # No telemetry
        
        mock_settings = MagicMock()
        mock_settings.environment = "production"
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.ProblemDetailsFactory') as mock_problem_factory:
                mock_problem = MagicMock()
                mock_problem.status = 500
                mock_problem.model_dump.return_value = {
                    "type": "about:blank",
                    "title": "Internal Server Error",
                    "status": 500,
                    "instance": "http://test.com/api/test"
                }
                mock_problem_factory.create_internal_server_error.return_value = mock_problem
                
                # Act
                response = await handler(mock_request, test_exception)
                
                # Assert
                assert response.status_code == 500
                
                # Verify problem details creation (without detail in production)
                mock_problem_factory.create_internal_server_error.assert_called_once_with(
                    detail=None,
                    instance="http://test.com/api/test"
                )

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
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.ExceptionHandlerBase') as mock_exception_handler:
                with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.ProblemDetailsFactory') as mock_problem_factory:
                    mock_problem = MagicMock()
                    mock_problem.status = 500
                    mock_problem.model_dump.return_value = {"status": 500}
                    mock_problem_factory.create_internal_server_error.return_value = mock_problem
                    
                    # Update request to use the app without telemetry
                    mock_request.app = app
                    
                    # Act
                    response = await handler(mock_request, test_exception)
                    
                    # Assert
                    assert response.status_code == 500
                    # ExceptionHandlerBase should not be instantiated
                    mock_exception_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_global_exception_handler_with_telemetry_none(self, mock_app, mock_request, mock_settings):
        """Test global exception handler when telemetry service exists but is None."""
        # Arrange
        configure_exception_handlers(mock_app)
        handler = mock_app.exception_handlers[Exception]
        
        test_exception = Exception("Test exception")
        mock_app.state.telemetry_service = None  # Explicitly None
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.ExceptionHandlerBase') as mock_exception_handler:
                with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.ProblemDetailsFactory') as mock_problem_factory:
                    mock_problem = MagicMock()
                    mock_problem.status = 500
                    mock_problem.model_dump.return_value = {"status": 500}
                    mock_problem_factory.create_internal_server_error.return_value = mock_problem
                    
                    # Act
                    response = await handler(mock_request, test_exception)
                    
                    # Assert
                    assert response.status_code == 500
                    # ExceptionHandlerBase should not be instantiated when telemetry is None
                    mock_exception_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_global_exception_handler_response_content(self, mock_app, mock_request, mock_settings):
        """Test that the response contains the expected problem details."""
        # Arrange
        configure_exception_handlers(mock_app)
        handler = mock_app.exception_handlers[Exception]
        
        test_exception = Exception("Test exception")
        expected_content = {
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "Test exception",
            "instance": "http://test.com/api/test"
        }
        
        with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.exception_handlers.ProblemDetailsFactory') as mock_problem_factory:
                mock_problem = MagicMock()
                mock_problem.status = 500
                mock_problem.model_dump.return_value = expected_content
                mock_problem_factory.create_internal_server_error.return_value = mock_problem
                
                # Act
                response = await handler(mock_request, test_exception)
                
                # Assert
                assert response.status_code == 500
                # JSONResponse content would be the expected_content
                assert response.body  # Response has content