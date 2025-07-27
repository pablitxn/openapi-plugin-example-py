"""Unit tests for dependency injection."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request
from openapi_plugin_common import AzureBlobService

from src.openapi_plugin_example_py.api.extensions.dependency_injection import (
    get_cache_service,
    get_blob_service,
    get_llm_provider,
    get_geney_client,
    get_sample_handler,
    get_ai_sample_handler,
    get_blob_sample_handler,
    get_create_plot_handler,
    get_cache_service_for_app,
    get_blob_service_for_app,
    get_llm_provider_for_app,
    get_geney_client_for_app,
    setup_dependencies,
)
from src.openapi_plugin_example_py.business_logic.handlers import (
    SampleHandler,
    AISampleHandler,
    BlobSampleHandler,
    CreatePlotHandler,
)


class TestDependencyInjection:
    """Test suite for dependency injection functions."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        app = FastAPI()
        app.state = MagicMock()
        app.state.settings = MagicMock()
        app.state.telemetry_service = MagicMock()
        app.state.command_invoker_factory = MagicMock()
        return app

    @pytest.fixture
    def mock_request(self, mock_app):
        """Create a mock request."""
        request = MagicMock(spec=Request)
        request.app = mock_app
        return request

    @pytest.mark.asyncio
    async def test_get_cache_service_with_redis(self, mock_request):
        """Test get_cache_service with Redis enabled."""
        # Arrange
        mock_request.app.state.settings.redis_url = "redis://localhost:6379"
        mock_request.app.state.settings.plugin_options.cache.enabled = True
        
        mock_redis_client = AsyncMock()
        
        async def async_from_url(url):
            return mock_redis_client
            
        with patch('redis.asyncio.from_url', new=async_from_url) as mock_redis:
            # Act
            result = await get_cache_service(mock_request)
            
            # Assert
            assert result == mock_redis_client

    @pytest.mark.asyncio
    async def test_get_cache_service_redis_connection_failure(self, mock_request):
        """Test get_cache_service when Redis connection fails."""
        # Arrange
        mock_request.app.state.settings.redis_url = "redis://localhost:6379"
        mock_request.app.state.settings.plugin_options.cache.enabled = True
        
        async def async_from_url_error(url):
            raise Exception("Connection failed")
            
        with patch('redis.asyncio.from_url', new=async_from_url_error):
            # Act
            result = await get_cache_service(mock_request)
            
            # Assert
            assert result is None
            mock_request.app.state.telemetry_service.log_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_service_disabled(self, mock_request):
        """Test get_cache_service when caching is disabled."""
        # Arrange
        mock_request.app.state.settings.redis_url = "redis://localhost:6379"
        mock_request.app.state.settings.plugin_options.cache.enabled = False
        
        # Act
        result = await get_cache_service(mock_request)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_blob_service_filesystem(self, mock_request):
        """Test get_blob_service with filesystem storage."""
        # Arrange
        mock_request.app.state.settings.use_filesystem_storage = True
        mock_request.app.state.settings.filesystem_storage_path = "/tmp/storage"
        
        # Act
        result = await get_blob_service(mock_request)
        
        # Assert
        assert result is not None
        assert result.__class__.__name__ == "FilesystemBlobService"

    @pytest.mark.asyncio
    async def test_get_blob_service_azure(self, mock_request):
        """Test get_blob_service with Azure Blob Storage."""
        # Arrange
        mock_request.app.state.settings.use_filesystem_storage = False
        mock_request.app.state.settings.blob_storage = MagicMock()
        mock_request.app.state.settings.blob_storage.connection_string = "DefaultEndpointsProtocol=https;..."
        
        with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.AzureBlobService') as mock_azure:
            mock_azure_service = MagicMock()
            mock_azure.return_value = mock_azure_service
            
            # Act
            result = await get_blob_service(mock_request)
            
            # Assert
            assert result == mock_azure_service
            mock_azure.assert_called_once_with("DefaultEndpointsProtocol=https;...")

    @pytest.mark.asyncio
    async def test_get_blob_service_none(self, mock_request):
        """Test get_blob_service when no storage is configured."""
        # Arrange
        mock_request.app.state.settings.use_filesystem_storage = False
        mock_request.app.state.settings.blob_storage = None
        
        # Act
        result = await get_blob_service(mock_request)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_llm_provider_configured(self, mock_request):
        """Test get_llm_provider when Azure OpenAI is configured."""
        # Arrange
        mock_azure_config = MagicMock()
        mock_azure_config.endpoint = "https://test.openai.azure.com"
        mock_azure_config.api_key = "test-key"
        mock_azure_config.deployment_name = "gpt-4"
        mock_request.app.state.settings.plugin_options.azure_openai = mock_azure_config
        mock_request.app.state.settings.plugin_options.openai = None
        
        with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.create_llm_provider') as mock_create_llm:
            mock_llm_provider = MagicMock()
            mock_create_llm.return_value = mock_llm_provider
            
            # Act
            result = await get_llm_provider(mock_request)
            
            # Assert
            assert result == mock_llm_provider
            mock_create_llm.assert_called_once_with(
                config=mock_azure_config,
                telemetry_service=mock_request.app.state.telemetry_service
            )

    @pytest.mark.asyncio
    async def test_get_llm_provider_not_configured(self, mock_request):
        """Test get_llm_provider when LLM is not configured."""
        # Arrange
        mock_request.app.state.settings.plugin_options.azure_openai = None
        mock_request.app.state.settings.plugin_options.openai = None
        
        # Act
        result = await get_llm_provider(mock_request)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_llm_provider_legacy_openai(self, mock_request):
        """Test get_llm_provider with legacy OpenAI configuration (returns None)."""
        # Arrange
        mock_openai_config = MagicMock()
        mock_openai_config.api_key = "test-key"
        mock_request.app.state.settings.plugin_options.azure_openai = None
        mock_request.app.state.settings.plugin_options.openai = mock_openai_config
        mock_request.app.state.telemetry_service = MagicMock()
        
        # Act
        result = await get_llm_provider(mock_request)
        
        # Assert
        assert result is None
        # Verify warning was logged
        mock_request.app.state.telemetry_service.log_warning.assert_called_once_with(
            "Using deprecated OpenAI configuration. Please migrate to Azure OpenAI."
        )

    @pytest.mark.asyncio
    async def test_get_geney_client_configured(self, mock_request):
        """Test get_geney_client when GenEY is configured."""
        # Arrange
        mock_request.app.state.settings.security.geney_client_id = "test-client-id"
        mock_request.app.state.settings.security.geney_api_domain = "https://api.geney.com"
        mock_request.app.state.settings.plugin_options.supported_file_types = ["pdf", "txt"]
        
        with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.GenEYClient') as mock_geney:
            mock_geney_client = MagicMock()
            mock_geney.return_value = mock_geney_client
            
            # Act
            result = await get_geney_client(mock_request)
            
            # Assert
            assert result == mock_geney_client
            mock_geney.assert_called_once_with(allowed_file_types=["pdf", "txt"])

    @pytest.mark.asyncio
    async def test_get_geney_client_not_configured(self, mock_request):
        """Test get_geney_client when GenEY is not configured."""
        # Arrange
        mock_request.app.state.settings.security.geney_client_id = None
        mock_request.app.state.settings.security.geney_api_domain = None
        
        # Act
        result = await get_geney_client(mock_request)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_sample_handler(self, mock_request):
        """Test get_sample_handler."""
        # Arrange
        mock_cache_service = MagicMock()
        
        with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.get_cache_service', return_value=mock_cache_service):
            # Act
            result = await get_sample_handler(mock_request, mock_cache_service)
            
            # Assert
            assert isinstance(result, SampleHandler)
            assert result._command_invoker_factory == mock_request.app.state.command_invoker_factory

    @pytest.mark.asyncio
    async def test_get_ai_sample_handler(self, mock_request):
        """Test get_ai_sample_handler."""
        # Arrange
        mock_cache_service = MagicMock()
        mock_openai_service = MagicMock()
        
        # Act
        result = await get_ai_sample_handler(mock_request, mock_cache_service, mock_openai_service)
        
        # Assert
        assert isinstance(result, AISampleHandler)
        assert result._command_invoker_factory == mock_request.app.state.command_invoker_factory

    @pytest.mark.asyncio
    async def test_get_blob_sample_handler(self, mock_request):
        """Test get_blob_sample_handler."""
        # Arrange
        mock_blob_service = MagicMock()
        
        # Act
        result = await get_blob_sample_handler(mock_request, mock_blob_service)
        
        # Assert
        assert isinstance(result, BlobSampleHandler)
        assert result._command_invoker_factory == mock_request.app.state.command_invoker_factory

    @pytest.mark.asyncio
    async def test_get_create_plot_handler(self, mock_request):
        """Test get_create_plot_handler."""
        # Arrange
        mock_blob_service = MagicMock()
        
        # Act
        result = await get_create_plot_handler(mock_request, mock_blob_service)
        
        # Assert
        assert isinstance(result, CreatePlotHandler)
        assert result._command_invoker_factory == mock_request.app.state.command_invoker_factory

    @pytest.mark.asyncio
    async def test_get_cache_service_for_app(self, mock_app):
        """Test get_cache_service_for_app."""
        # Arrange
        mock_app.state.settings.redis_url = "redis://localhost:6379"
        mock_app.state.settings.plugin_options.cache.enabled = True
        
        mock_redis_client = AsyncMock()
        
        async def async_from_url(url):
            return mock_redis_client
            
        with patch('redis.asyncio.from_url', new=async_from_url):
            # Act
            result = await get_cache_service_for_app(mock_app)
            
            # Assert
            assert result == mock_redis_client

    @pytest.mark.asyncio
    async def test_get_blob_service_for_app_filesystem(self, mock_app):
        """Test get_blob_service_for_app with filesystem storage."""
        # Arrange
        mock_app.state.settings.use_filesystem_storage = True
        mock_app.state.settings.filesystem_storage_path = "/tmp/storage"
        
        # Act
        result = await get_blob_service_for_app(mock_app)
        
        # Assert
        assert result is not None
        assert result.__class__.__name__ == "FilesystemBlobService"

    @pytest.mark.asyncio
    async def test_get_llm_provider_for_app(self, mock_app):
        """Test get_llm_provider_for_app."""
        # Arrange
        mock_azure_config = MagicMock()
        mock_azure_config.endpoint = "https://test.openai.azure.com"
        mock_azure_config.api_key = "test-key"
        mock_azure_config.deployment_name = "gpt-4"
        mock_app.state.settings.plugin_options.azure_openai = mock_azure_config
        mock_app.state.settings.plugin_options.openai = None
        
        with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.create_llm_provider') as mock_create_llm:
            mock_llm_provider = MagicMock()
            mock_create_llm.return_value = mock_llm_provider
            
            # Act
            result = await get_llm_provider_for_app(mock_app)
            
            # Assert
            assert result == mock_llm_provider

    @pytest.mark.asyncio
    async def test_get_geney_client_for_app(self, mock_app):
        """Test get_geney_client_for_app."""
        # Arrange
        mock_app.state.settings.security.geney_client_id = "test-client-id"
        mock_app.state.settings.security.geney_api_domain = "https://api.geney.com"
        mock_app.state.settings.plugin_options.supported_file_types = ["pdf", "txt"]
        
        with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.GenEYClient') as mock_geney:
            mock_geney_client = MagicMock()
            mock_geney.return_value = mock_geney_client
            
            # Act
            result = await get_geney_client_for_app(mock_app)
            
            # Assert
            assert result == mock_geney_client

    @pytest.mark.asyncio
    async def test_get_cache_service_for_app_connection_failure(self, mock_app):
        """Test get_cache_service_for_app when Redis connection fails."""
        # Arrange
        mock_app.state.settings.redis_url = "redis://localhost:6379"
        mock_app.state.settings.plugin_options.cache.enabled = True
        
        async def async_from_url_error(url):
            raise Exception("Connection failed")
            
        with patch('redis.asyncio.from_url', new=async_from_url_error):
            # Act
            result = await get_cache_service_for_app(mock_app)
            
            # Assert
            assert result is None
            mock_app.state.telemetry_service.log_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_blob_service_for_app_azure(self, mock_app):
        """Test get_blob_service_for_app with Azure storage."""
        # Arrange
        mock_app.state.settings.use_filesystem_storage = False
        mock_app.state.settings.filesystem_storage_path = None
        mock_app.state.settings.blob_storage = MagicMock()
        mock_app.state.settings.blob_storage.connection_string = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test=="
        
        with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.AzureBlobService') as mock_azure:
            mock_azure_service = MagicMock()
            mock_azure.return_value = mock_azure_service
            
            # Act
            result = await get_blob_service_for_app(mock_app)
            
            # Assert
            assert result == mock_azure_service
            mock_azure.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_blob_service_for_app_none(self, mock_app):
        """Test get_blob_service_for_app when no storage is configured."""
        # Arrange
        mock_app.state.settings.use_filesystem_storage = False
        mock_app.state.settings.filesystem_storage_path = None
        mock_app.state.settings.blob_storage = None
        
        # Act
        result = await get_blob_service_for_app(mock_app)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_llm_provider_for_app_not_configured(self, mock_app):
        """Test get_llm_provider_for_app when LLM is not configured."""
        # Arrange
        mock_app.state.settings.plugin_options.azure_openai = None
        mock_app.state.settings.plugin_options.openai = None
        
        # Act
        result = await get_llm_provider_for_app(mock_app)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_geney_client_for_app_not_configured(self, mock_app):
        """Test get_geney_client_for_app when GenEY is not configured."""
        # Arrange
        mock_app.state.settings.security.geney_client_id = None
        mock_app.state.settings.security.geney_api_domain = None
        
        # Act
        result = await get_geney_client_for_app(mock_app)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_setup_dependencies(self, mock_app):
        """Test setup_dependencies."""
        # Arrange
        mock_app.dependency_overrides = {}
        
        with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.get_cache_service_for_app') as mock_cache:
            with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.get_blob_service_for_app') as mock_blob:
                with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.get_llm_provider_for_app') as mock_openai:
                    with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.get_geney_client_for_app') as mock_geney:
                        mock_cache.return_value = MagicMock()
                        mock_blob.return_value = MagicMock()
                        mock_openai.return_value = MagicMock()
                        mock_geney.return_value = MagicMock()
                        
                        # Act
                        await setup_dependencies(mock_app)
                        
                        # Assert
                        assert SampleHandler in mock_app.dependency_overrides
                        assert AISampleHandler in mock_app.dependency_overrides
                        assert BlobSampleHandler in mock_app.dependency_overrides
                        assert CreatePlotHandler in mock_app.dependency_overrides
                        assert hasattr(mock_app.state, 'cache_service')
                        assert hasattr(mock_app.state, 'blob_service')
                        assert hasattr(mock_app.state, 'openai_service')
                        assert hasattr(mock_app.state, 'geney_client')