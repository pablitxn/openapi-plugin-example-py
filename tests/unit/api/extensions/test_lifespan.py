"""Unit tests for lifespan management."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
import logging

from src.openapi_plugin_example_py.api.extensions.app_lifespan import ExamplePluginLifespanManager


class TestExamplePluginLifespanManager:
    """Test suite for ExamplePluginLifespanManager."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        app = FastAPI()
        app.state = MagicMock()
        return app

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.environment = "test"
        settings.use_filesystem_storage = True
        settings.filesystem_storage_path = "/tmp/test"
        settings.bypass_auth = False
        settings.telemetry.enabled = True
        settings.telemetry.connection_string = "InstrumentationKey=test-key"
        settings.telemetry.service_name = "TestService"
        settings.telemetry.logger_name = "test.logger"
        settings.plugin_options.openai = MagicMock()
        settings.plugin_options.openai.api_key = "test-openai-key"
        settings.plugin_options.azure_openai = None
        return settings

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        logger = MagicMock()
        logger.info = MagicMock()
        logger.error = MagicMock()
        logger.warning = MagicMock()
        return logger

    @pytest.mark.asyncio
    async def test_startup_with_telemetry_enabled(self, mock_app, mock_settings, mock_logger):
        """Test startup with telemetry enabled."""
        with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.AzureMonitorTelemetryService') as mock_telemetry:
                mock_telemetry_instance = MagicMock()
                mock_telemetry.return_value = mock_telemetry_instance
                
                with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.setup_dependencies') as mock_setup:
                    mock_setup.return_value = None
                    
                    # Create manager with mock logger
                    manager = ExamplePluginLifespanManager()
                    manager.logger = mock_logger
                    
                    # Run startup
                    await manager.startup(mock_app)
                    
                    # Verify app state was set up
                    assert mock_app.state.settings == mock_settings
                    assert mock_app.state.telemetry_service == mock_telemetry_instance
                    
                    # Verify telemetry was initialized
                    mock_telemetry.assert_called_once_with(
                        connection_string="InstrumentationKey=test-key",
                        service_name="TestService",
                        logger_name="test.logger"
                    )
                    
                    # Verify setup_dependencies was called
                    mock_setup.assert_called_once_with(mock_app)
                    
                    # Verify logging
                    mock_logger.info.assert_any_call("Telemetry service initialized")

    @pytest.mark.asyncio
    async def test_startup_with_telemetry_disabled(self, mock_app, mock_settings, mock_logger):
        """Test startup with telemetry disabled."""
        mock_settings.telemetry.enabled = False
        
        with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.setup_dependencies') as mock_setup:
                mock_setup.return_value = None
                
                # Create manager
                manager = ExamplePluginLifespanManager()
                manager.logger = mock_logger
                
                # Run startup
                await manager.startup(mock_app)
                
                # Verify telemetry is None when disabled
                assert mock_app.state.telemetry_service is None
                
                # Verify setup_dependencies was still called
                mock_setup.assert_called_once_with(mock_app)

    @pytest.mark.asyncio
    async def test_startup_telemetry_initialization_failure(self, mock_app, mock_settings, mock_logger):
        """Test startup when telemetry initialization fails."""
        with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.AzureMonitorTelemetryService') as mock_telemetry:
                # Make telemetry initialization fail
                mock_telemetry.side_effect = Exception("Telemetry init failed")
                
                with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.setup_dependencies') as mock_setup:
                    mock_setup.return_value = None
                    
                    # Create manager
                    manager = ExamplePluginLifespanManager()
                    manager.logger = mock_logger
                    
                    # Run startup
                    await manager.startup(mock_app)
                    
                    # Verify telemetry is None when initialization fails
                    assert mock_app.state.telemetry_service is None
                    
                    # Verify error was logged
                    mock_logger.error.assert_called_with("Failed to initialize telemetry: Telemetry init failed")

    @pytest.mark.asyncio
    async def test_startup_with_empty_connection_string(self, mock_app, mock_settings, mock_logger):
        """Test startup when telemetry connection string is empty."""
        mock_settings.telemetry.connection_string = ""
        
        with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.setup_dependencies') as mock_setup:
                mock_setup.return_value = None
                
                # Create manager
                manager = ExamplePluginLifespanManager()
                manager.logger = mock_logger
                
                # Run startup
                await manager.startup(mock_app)
                
                # Verify telemetry is None when connection string is empty
                assert mock_app.state.telemetry_service is None

    @pytest.mark.asyncio
    async def test_startup_debug_logging(self, mock_app, mock_settings, mock_logger):
        """Test that startup logs debug information."""
        with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.AzureMonitorTelemetryService'):
                with patch('src.openapi_plugin_example_py.api.extensions.app_lifespan.setup_dependencies') as mock_setup:
                    mock_setup.return_value = None
                    
                    # Set up mock app state with services
                    mock_app.state.blob_service = MagicMock()
                    mock_app.state.llm_provider = MagicMock()
                    mock_app.state.cache_service = MagicMock()
                    
                    # Create manager
                    manager = ExamplePluginLifespanManager()
                    manager.logger = mock_logger
                    
                    # Run startup
                    await manager.startup(mock_app)
                    
                    # Verify debug logging
                    mock_logger.info.assert_any_call("Blob service configured: True")
                    mock_logger.info.assert_any_call(f"Blob service type: {type(mock_app.state.blob_service)}")
                    mock_logger.info.assert_any_call("LLM provider configured: True")
                    mock_logger.info.assert_any_call("Cache service configured: True")

    @pytest.mark.asyncio
    async def test_shutdown(self, mock_app):
        """Test shutdown method."""
        # Create manager
        manager = ExamplePluginLifespanManager()
        
        # Run shutdown (should complete without error)
        await manager.shutdown(mock_app)
        
        # Since shutdown is currently a no-op, just verify it runs
        assert True