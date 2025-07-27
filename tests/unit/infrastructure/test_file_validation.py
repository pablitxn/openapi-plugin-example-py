"""Unit tests for file validation module."""
import pytest
from unittest.mock import patch, MagicMock

from src.openapi_plugin_example_py.infrastructure.file_validation import (
    create_geney_validator,
    DEFAULT_ALLOWED_TYPES
)


class TestFileValidation:
    """Test suite for file validation module."""

    def test_default_allowed_types(self):
        """Test default allowed file types constant."""
        # Assert
        assert DEFAULT_ALLOWED_TYPES == ["pdf", "txt", "docx", "json", "csv", "xlsx"]
        assert isinstance(DEFAULT_ALLOWED_TYPES, list)
        assert len(DEFAULT_ALLOWED_TYPES) == 6

    def test_create_geney_validator_with_defaults(self):
        """Test creating validator with default allowed types."""
        # Arrange
        mock_validator = MagicMock()
        
        with patch('openapi_plugin_common.FileTypeValidator.create_for_geney', 
                   return_value=mock_validator) as mock_create:
            # Act
            result = create_geney_validator()

            # Assert
            assert result == mock_validator
            mock_create.assert_called_once_with(
                allowed_types=DEFAULT_ALLOWED_TYPES
            )

    def test_create_geney_validator_with_custom_types(self):
        """Test creating validator with custom allowed types."""
        # Arrange
        custom_types = ["jpg", "png", "gif"]
        mock_validator = MagicMock()
        
        with patch('openapi_plugin_common.FileTypeValidator.create_for_geney', 
                   return_value=mock_validator) as mock_create:
            # Act
            result = create_geney_validator(allowed_types=custom_types)

            # Assert
            assert result == mock_validator
            mock_create.assert_called_once_with(
                allowed_types=custom_types
            )

    def test_create_geney_validator_with_empty_list(self):
        """Test creating validator with empty list."""
        # Arrange
        empty_types = []
        mock_validator = MagicMock()
        
        with patch('openapi_plugin_common.FileTypeValidator.create_for_geney', 
                   return_value=mock_validator) as mock_create:
            # Act
            result = create_geney_validator(allowed_types=empty_types)

            # Assert
            assert result == mock_validator
            mock_create.assert_called_once_with(
                allowed_types=empty_types
            )

    def test_create_geney_validator_with_none_uses_defaults(self):
        """Test that None parameter uses default types."""
        # Arrange
        mock_validator = MagicMock()
        
        with patch('openapi_plugin_common.FileTypeValidator.create_for_geney', 
                   return_value=mock_validator) as mock_create:
            # Act
            result = create_geney_validator(allowed_types=None)

            # Assert
            assert result == mock_validator
            mock_create.assert_called_once_with(
                allowed_types=DEFAULT_ALLOWED_TYPES
            )