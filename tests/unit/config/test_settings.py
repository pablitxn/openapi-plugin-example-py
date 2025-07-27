"""Unit tests for settings configuration."""
import json
import pytest
from unittest.mock import patch, MagicMock

from src.openapi_plugin_example_py.config.settings import (
    AppSettings,
    get_settings
)
from src.openapi_plugin_example_py.business_logic.options import ExamplePluginOptions
from openapi_plugin_common import SchemasConfig


class TestAppSettings:
    """Test suite for AppSettings."""

    def test_default_initialization(self):
        """Test AppSettings with default values."""
        # Act
        settings = AppSettings()

        # Assert
        assert settings.api_prefix == "/api/plugin/ExamplePlugin"
        assert isinstance(settings.plugin_options, ExamplePluginOptions)

    def test_custom_api_prefix(self):
        """Test AppSettings with custom API prefix."""
        # Act
        settings = AppSettings(api_prefix="/custom/api")

        # Assert
        assert settings.api_prefix == "/custom/api"

    def test_plugin_options_as_dict(self):
        """Test AppSettings with plugin options as dictionary."""
        # Arrange
        plugin_options_dict = {
            "schemas": {},  # Required field
            "max_file_size_mb": 20,
            "supported_file_types": ["pdf", "docx"],
            "enable_caching": False
        }

        # Act
        settings = AppSettings(plugin_options=plugin_options_dict)

        # Assert
        assert isinstance(settings.plugin_options, ExamplePluginOptions)
        assert settings.plugin_options.max_file_size_mb == 20
        assert settings.plugin_options.supported_file_types == ["pdf", "docx"]
        assert settings.plugin_options.enable_caching is False

    def test_plugin_options_as_json_string(self):
        """Test AppSettings with plugin options as JSON string."""
        # Arrange
        plugin_options_json = json.dumps({
            "schemas": {},  # Required field
            "max_file_size_mb": 15,
            "supported_file_types": ["txt", "csv"],
            "enable_caching": True
        })

        # Act
        settings = AppSettings(plugin_options=plugin_options_json)

        # Assert
        assert isinstance(settings.plugin_options, ExamplePluginOptions)
        assert settings.plugin_options.max_file_size_mb == 15
        assert settings.plugin_options.supported_file_types == ["txt", "csv"]
        assert settings.plugin_options.enable_caching is True

    def test_plugin_options_as_object(self):
        """Test AppSettings with plugin options as ExamplePluginOptions object."""
        # Arrange
        plugin_options = ExamplePluginOptions(
            schemas=SchemasConfig(),  # Required field
            max_file_size_mb=25,
            supported_file_types=["jpg", "png"],
            enable_caching=False
        )

        # Act
        settings = AppSettings(plugin_options=plugin_options)

        # Assert
        assert settings.plugin_options == plugin_options
        assert settings.plugin_options.max_file_size_mb == 25

    def test_invalid_plugin_options_json(self):
        """Test AppSettings with invalid JSON string for plugin options."""
        # Arrange
        invalid_json = "{ invalid json"

        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            AppSettings(plugin_options=invalid_json)

    def test_inheritance_from_base_app_settings(self):
        """Test that AppSettings inherits from BaseAppSettings."""
        # Act
        settings = AppSettings()

        # Assert - verify some base settings exist
        assert hasattr(settings, 'environment')
        assert hasattr(settings, 'bypass_auth')
        assert hasattr(settings, 'security')


class TestGetSettings:
    """Test suite for get_settings function."""

    def test_get_settings_returns_app_settings(self):
        """Test that get_settings returns AppSettings instance."""
        # Arrange
        mock_settings = AppSettings()
        
        with patch('src.openapi_plugin_example_py.config.settings.get_base_settings', 
                   return_value=mock_settings) as mock_get_base:
            # Act
            result = get_settings()

            # Assert
            assert result == mock_settings
            assert isinstance(result, AppSettings)
            mock_get_base.assert_called_once_with(AppSettings)

    def test_get_settings_with_environment_variables(self):
        """Test get_settings with environment variables."""
        # Arrange
        mock_settings = AppSettings(
            api_prefix="/env/api",
            plugin_options=ExamplePluginOptions(max_file_size_mb=30)
        )
        
        with patch('src.openapi_plugin_example_py.config.settings.get_base_settings', 
                   return_value=mock_settings):
            # Act
            result = get_settings()

            # Assert
            assert result.api_prefix == "/env/api"
            assert result.plugin_options.max_file_size_mb == 30