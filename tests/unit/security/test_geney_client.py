"""Unit tests for GenEYClient."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.openapi_plugin_example_py.infrastructure.security.geney_client import GenEYClient


class TestGenEYClient:
    """Test suite for GenEYClient."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.security.tenant_id = "test-tenant-id"
        settings.security.client_secret = "test-client-secret"
        settings.security.client_id = "test-client-id"
        settings.security.geney_client_id = "test-geney-client-id"
        settings.security.geney_api_domain = "https://geney-api.example.com"
        settings.plugin_options.supported_file_types = ["pdf", "txt", "xlsx"]
        return settings

    @pytest.fixture
    def mock_file_validator(self):
        """Create mock file validator."""
        validator = MagicMock()
        validator.validate = MagicMock()
        return validator

    def test_initialization_default_file_types(self, mock_settings, mock_file_validator):
        """Test GenEYClient initialization with default file types."""
        # Arrange
        with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.get_settings', 
                   return_value=mock_settings):
            with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.create_geney_validator', 
                       return_value=mock_file_validator) as mock_create_validator:
                # Act
                client = GenEYClient()

                # Assert
                assert client._settings == mock_settings
                assert client.file_validator == mock_file_validator
                mock_create_validator.assert_called_once_with(["pdf", "txt", "xlsx"])

    def test_initialization_custom_file_types(self, mock_settings, mock_file_validator):
        """Test GenEYClient initialization with custom file types."""
        # Arrange
        custom_types = ["doc", "docx", "pdf"]
        
        with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.get_settings', 
                   return_value=mock_settings):
            with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.create_geney_validator', 
                       return_value=mock_file_validator) as mock_create_validator:
                # Act
                client = GenEYClient(allowed_file_types=custom_types)

                # Assert
                mock_create_validator.assert_called_once_with(custom_types)

    def test_client_id_property(self, mock_settings):
        """Test client_id property."""
        # Arrange
        with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.get_settings', 
                   return_value=mock_settings):
            client = GenEYClient()

            # Act
            result = client.client_id

            # Assert
            assert result == "test-client-id"

    def test_geney_client_id_property(self, mock_settings):
        """Test geney_client_id property."""
        # Arrange
        with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.get_settings', 
                   return_value=mock_settings):
            client = GenEYClient()

            # Act
            result = client.geney_client_id

            # Assert
            assert result == "test-geney-client-id"

    def test_geney_api_domain_property(self, mock_settings):
        """Test geney_api_domain property."""
        # Arrange
        with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.get_settings', 
                   return_value=mock_settings):
            client = GenEYClient()

            # Act
            result = client.geney_api_domain

            # Assert
            assert result == "https://geney-api.example.com"

    @pytest.mark.asyncio
    async def test_get_file_from_chat_validated_success(self, mock_settings, mock_file_validator):
        """Test successful file retrieval with validation."""
        # Arrange
        expected_content = b"File content"
        
        with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.get_settings', 
                   return_value=mock_settings):
            with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.create_geney_validator', 
                       return_value=mock_file_validator):
                with patch('openapi_plugin_common.GenEYClientBase.get_file_from_chat', 
                           new_callable=AsyncMock, 
                           return_value=expected_content) as mock_get_file:
                    client = GenEYClient()

                    # Act
                    result = await client.get_file_from_chat_validated(
                        chat_id="test-chat-123",
                        file_name="document.pdf",
                        user_token="test-token"
                    )

                    # Assert
                    assert result == expected_content
                    mock_file_validator.validate.assert_called_once_with("document.pdf")
                    mock_get_file.assert_called_once_with(
                        "test-chat-123",
                        "document.pdf",
                        "test-token"
                    )

    @pytest.mark.asyncio
    async def test_get_file_from_chat_validated_invalid_type(self, mock_settings, mock_file_validator):
        """Test file retrieval with invalid file type."""
        # Arrange
        mock_file_validator.validate.side_effect = ValueError("Invalid file type")
        
        with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.get_settings', 
                   return_value=mock_settings):
            with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.create_geney_validator', 
                       return_value=mock_file_validator):
                client = GenEYClient()

                # Act & Assert
                with pytest.raises(ValueError, match="Invalid file type"):
                    await client.get_file_from_chat_validated(
                        chat_id="test-chat-123",
                        file_name="malicious.exe",
                        user_token="test-token"
                    )

                # Verify validation was called but not the parent method
                mock_file_validator.validate.assert_called_once_with("malicious.exe")

    @pytest.mark.asyncio
    async def test_get_file_from_chat_validated_file_not_found(self, mock_settings, mock_file_validator):
        """Test file retrieval when file is not found."""
        # Arrange
        with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.get_settings', 
                   return_value=mock_settings):
            with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.create_geney_validator', 
                       return_value=mock_file_validator):
                with patch('openapi_plugin_common.GenEYClientBase.get_file_from_chat', 
                           new_callable=AsyncMock, 
                           side_effect=FileNotFoundError("File not found")):
                    client = GenEYClient()

                    # Act & Assert
                    with pytest.raises(FileNotFoundError, match="File not found"):
                        await client.get_file_from_chat_validated(
                            chat_id="test-chat-123",
                            file_name="missing.pdf",
                            user_token="test-token"
                        )

    def test_parent_class_initialization(self, mock_settings):
        """Test that parent class is properly initialized."""
        # Arrange
        with patch('src.openapi_plugin_example_py.infrastructure.security.geney_client.get_settings', 
                   return_value=mock_settings):
            with patch('openapi_plugin_common.GenEYClientBase.__init__') as mock_parent_init:
                # Act
                client = GenEYClient()

                # Assert
                mock_parent_init.assert_called_once_with(
                    tenant_id="test-tenant-id",
                    client_secret="test-client-secret"
                )