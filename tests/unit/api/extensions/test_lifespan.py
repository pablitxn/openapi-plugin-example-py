"""Unit tests for lifespan management."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
import logging

from src.openapi_plugin_example_py.api.extensions.app_lifespan import ExamplePluginLifespanManager


class TestLifespan:
    """Test suite for lifespan management."""

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

    @pytest.mark.asyncio
    async def test_lifespan_with_telemetry_enabled(self, mock_app, mock_settings):
        """Test lifespan with telemetry enabled."""
        with patch('src.openapi_plugin_example_py.api.extensions.lifespan.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.lifespan.AzureMonitorTelemetryService') as mock_telemetry:
                mock_telemetry_instance = MagicMock()
                mock_telemetry_instance.flush = MagicMock()
                mock_telemetry.return_value = mock_telemetry_instance
                
                with patch('src.openapi_plugin_example_py.api.extensions.lifespan.setup_dependencies') as mock_setup:
                    mock_setup.return_value = None
                    mock_app.state.cache_service = MagicMock()
                    mock_app.state.blob_service = MagicMock()
                    mock_app.state.llm_provider = MagicMock()
                    
                    with patch('src.openapi_plugin_example_py.api.extensions.lifespan.CustomCommandInvokerFactory') as mock_factory:
                        mock_factory_instance = MagicMock()
                        mock_factory.return_value = mock_factory_instance
                        
                        # Use the lifespan context manager
                        async with lifespan(mock_app):
                            # Verify app state was set up
                            assert mock_app.state.settings == mock_settings
                            assert mock_app.state.telemetry_service == mock_telemetry_instance
                            assert mock_app.state.command_invoker_factory == mock_factory_instance
                            
                            # Verify telemetry was initialized
                            mock_telemetry.assert_called_once_with(
                                connection_string="InstrumentationKey=test-key",
                                service_name="TestService",
                                logger_name="test.logger"
                            )
                            
                            # Verify setup_dependencies was called
                            mock_setup.assert_called_once_with(mock_app)
                            
                            # Verify command factory was created
                            mock_factory.assert_called_once_with(
                                telemetry_service=mock_telemetry_instance,
                                cache_service=mock_app.state.cache_service,
                                blob_service=mock_app.state.blob_service,
                                llm_provider=mock_app.state.llm_provider,
                                enable_command_logging=True,
                                session_id=None,
                                user_id=None
                            )
                        
                        # Verify cleanup after yield
                        mock_telemetry_instance.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_with_telemetry_disabled(self, mock_app, mock_settings):
        """Test lifespan with telemetry disabled."""
        mock_settings.telemetry.enabled = False
        
        with patch('src.openapi_plugin_example_py.api.extensions.lifespan.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.lifespan.setup_dependencies') as mock_setup:
                mock_setup.return_value = None
                mock_app.state.cache_service = None
                mock_app.state.blob_service = None
                mock_app.state.llm_provider = None
                
                with patch('src.openapi_plugin_example_py.api.extensions.lifespan.CustomCommandInvokerFactory') as mock_factory:
                    mock_factory_instance = MagicMock()
                    mock_factory.return_value = mock_factory_instance
                    
                    async with lifespan(mock_app):
                        # Verify telemetry is None when disabled
                        assert mock_app.state.telemetry_service is None
                        
                        # Verify command factory was created with None telemetry
                        mock_factory.assert_called_once_with(
                            telemetry_service=None,
                            cache_service=None,
                            blob_service=None,
                            llm_provider=None,
                            enable_command_logging=True,
                            session_id=None,
                            user_id=None
                        )

    @pytest.mark.asyncio
    async def test_lifespan_telemetry_initialization_failure(self, mock_app, mock_settings):
        """Test lifespan when telemetry initialization fails."""
        with patch('src.openapi_plugin_example_py.api.extensions.lifespan.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.lifespan.AzureMonitorTelemetryService') as mock_telemetry:
                # Make telemetry initialization fail
                mock_telemetry.side_effect = Exception("Telemetry init failed")
                
                with patch('src.openapi_plugin_example_py.api.extensions.lifespan.setup_dependencies') as mock_setup:
                    mock_setup.return_value = None
                    mock_app.state.cache_service = None
                    mock_app.state.blob_service = None
                    mock_app.state.llm_provider = None
                    
                    with patch('src.openapi_plugin_example_py.api.extensions.lifespan.CustomCommandInvokerFactory') as mock_factory:
                        mock_factory_instance = MagicMock()
                        mock_factory.return_value = mock_factory_instance
                        
                        with patch('src.openapi_plugin_example_py.api.extensions.lifespan.logger') as mock_logger:
                            async with lifespan(mock_app):
                                # Verify telemetry is None when initialization fails
                                assert mock_app.state.telemetry_service is None
                                
                                # Verify error was logged
                                mock_logger.error.assert_called_with("Failed to initialize telemetry: Telemetry init failed")

    @pytest.mark.asyncio
    async def test_lifespan_with_no_openai_key(self, mock_app, mock_settings):
        """Test lifespan when OpenAI is not configured."""
        mock_settings.plugin_options.openai = None
        
        with patch('src.openapi_plugin_example_py.api.extensions.lifespan.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.lifespan.AzureMonitorTelemetryService') as mock_telemetry:
                mock_telemetry_instance = MagicMock()
                mock_telemetry.return_value = mock_telemetry_instance
                
                with patch('src.openapi_plugin_example_py.api.extensions.lifespan.setup_dependencies') as mock_setup:
                    mock_setup.return_value = None
                    mock_app.state.cache_service = None
                    mock_app.state.blob_service = None
                    mock_app.state.llm_provider = None
                    
                    with patch('src.openapi_plugin_example_py.api.extensions.lifespan.CustomCommandInvokerFactory') as mock_factory:
                        with patch('src.openapi_plugin_example_py.api.extensions.lifespan.logger') as mock_logger:
                            async with lifespan(mock_app):
                                # Verify the correct log message for OpenAI config
                                log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                                assert any("OpenAI API key configured: False" in msg for msg in log_calls)

    @pytest.mark.asyncio
    async def test_lifespan_with_empty_connection_string(self, mock_app, mock_settings):
        """Test lifespan when telemetry connection string is empty."""
        mock_settings.telemetry.connection_string = ""
        
        with patch('src.openapi_plugin_example_py.api.extensions.lifespan.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.lifespan.setup_dependencies') as mock_setup:
                mock_setup.return_value = None
                mock_app.state.cache_service = None
                mock_app.state.blob_service = None
                mock_app.state.llm_provider = None
                
                with patch('src.openapi_plugin_example_py.api.extensions.lifespan.CustomCommandInvokerFactory') as mock_factory:
                    async with lifespan(mock_app):
                        # Verify telemetry is None when connection string is empty
                        assert mock_app.state.telemetry_service is None

    @pytest.mark.asyncio
    async def test_lifespan_logging(self, mock_app, mock_settings):
        """Test that lifespan logs all expected messages."""
        with patch('src.openapi_plugin_example_py.api.extensions.lifespan.get_settings') as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            
            with patch('src.openapi_plugin_example_py.api.extensions.lifespan.AzureMonitorTelemetryService') as mock_telemetry:
                mock_telemetry_instance = MagicMock()
                mock_telemetry.return_value = mock_telemetry_instance
                
                with patch('src.openapi_plugin_example_py.api.extensions.lifespan.setup_dependencies') as mock_setup:
                    mock_setup.return_value = None
                    mock_app.state.cache_service = MagicMock()
                    mock_app.state.blob_service = MagicMock()
                    mock_app.state.llm_provider = MagicMock()
                    
                    with patch('src.openapi_plugin_example_py.api.extensions.lifespan.CustomCommandInvokerFactory'):
                        with patch('src.openapi_plugin_example_py.api.extensions.lifespan.logger') as mock_logger:
                            async with lifespan(mock_app):
                                pass
                            
                            # Verify all expected log messages
                            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                            
                            assert "Starting up Example Plugin..." in log_calls
                            assert "Telemetry service initialized" in log_calls
                            assert "Settings loaded - environment: test" in log_calls
                            assert "Use filesystem storage: True" in log_calls
                            assert "Filesystem storage path: /tmp/test" in log_calls
                            assert "Bypass auth: False" in log_calls
                            assert "Example Plugin started successfully" in log_calls
                            assert "Blob service configured: True" in log_calls
                            assert any("Blob service type:" in msg for msg in log_calls)
                            assert "LLM provider configured: True" in log_calls
                            assert "Cache service configured: True" in log_calls
                            assert "Shutting down Example Plugin..." in log_calls
                            assert "Example Plugin shut down successfully" in log_calls