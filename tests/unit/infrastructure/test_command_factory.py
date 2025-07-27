"""Unit tests for CustomCommandInvokerFactory."""
import pytest
from unittest.mock import MagicMock, patch

from openapi_plugin_common import CommandBase, CommandInvokerFactory
from src.openapi_plugin_example_py.infrastructure.command_factory import (
    CustomCommandInvokerFactory
)
from src.openapi_plugin_example_py.business_logic.commands import (
    AISampleCommand,
    BlobSampleCommand,
    CreatePlotCommand,
    SampleCommand
)


class TestCustomCommandInvokerFactory:
    """Test suite for CustomCommandInvokerFactory."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            'telemetry_service': MagicMock(name='telemetry_service'),
            'cache_service': MagicMock(name='cache_service'),
            'blob_service': MagicMock(name='blob_service'),
            'openai_service': MagicMock(name='openai_service')
        }

    @pytest.fixture
    def command_factory(self, mock_services):
        """Create a CustomCommandInvokerFactory instance."""
        return CustomCommandInvokerFactory(
            telemetry_service=mock_services['telemetry_service'],
            cache_service=mock_services['cache_service'],
            blob_service=mock_services['blob_service'],
            openai_service=mock_services['openai_service']
        )

    def test_initialization(self, mock_services):
        """Test factory initialization."""
        # Act
        factory = CustomCommandInvokerFactory(
            telemetry_service=mock_services['telemetry_service'],
            cache_service=mock_services['cache_service'],
            blob_service=mock_services['blob_service'],
            openai_service=mock_services['openai_service']
        )

        # Assert
        assert factory._telemetry_service == mock_services['telemetry_service']
        assert factory._cache_service == mock_services['cache_service']
        assert factory._blob_service == mock_services['blob_service']
        assert factory._openai_service == mock_services['openai_service']

    def test_create_sample_command(self, command_factory, mock_services):
        """Test creating SampleCommand."""
        # Act
        with patch('builtins.print'):  # Suppress debug prints
            command = command_factory.create(SampleCommand)

        # Assert
        assert isinstance(command, SampleCommand)
        assert command._telemetry_service == mock_services['telemetry_service']
        assert command._cache_service == mock_services['cache_service']

    def test_create_blob_sample_command(self, command_factory, mock_services):
        """Test creating BlobSampleCommand."""
        # Act
        with patch('builtins.print'):  # Suppress debug prints
            command = command_factory.create(BlobSampleCommand)

        # Assert
        assert isinstance(command, BlobSampleCommand)
        assert command._telemetry_service == mock_services['telemetry_service']
        assert command._blob_service == mock_services['blob_service']

    def test_create_ai_sample_command(self, command_factory, mock_services):
        """Test creating AISampleCommand."""
        # Act
        with patch('builtins.print'):  # Suppress debug prints
            command = command_factory.create(AISampleCommand)

        # Assert
        assert isinstance(command, AISampleCommand)
        assert command._telemetry_service == mock_services['telemetry_service']
        assert command._cache_service == mock_services['cache_service']
        assert command._openai_service == mock_services['openai_service']

    def test_create_create_plot_command(self, command_factory, mock_services):
        """Test creating CreatePlotCommand."""
        # Act
        with patch('builtins.print'):  # Suppress debug prints
            command = command_factory.create(CreatePlotCommand)

        # Assert
        assert isinstance(command, CreatePlotCommand)
        assert command._telemetry_service == mock_services['telemetry_service']
        assert command._blob_service == mock_services['blob_service']

    def test_create_unknown_command(self, command_factory):
        """Test creating unknown command falls back to parent."""
        # Arrange
        class UnknownCommand(CommandBase):
            async def execute_command_async(self, context):
                return "executed"

        # Act
        with patch('builtins.print'):  # Suppress debug prints
            with patch.object(
                CommandInvokerFactory,
                'create',
                return_value=UnknownCommand()
            ) as mock_parent_create:
                command = command_factory.create(UnknownCommand)

        # Assert
        assert isinstance(command, UnknownCommand)
        mock_parent_create.assert_called_once_with(UnknownCommand)

    def test_create_with_none_services(self):
        """Test factory works with None services."""
        # Arrange
        factory = CustomCommandInvokerFactory(
            telemetry_service=None,
            cache_service=None,
            blob_service=None,
            openai_service=None
        )

        # Act
        with patch('builtins.print'):  # Suppress debug prints
            sample_command = factory.create(SampleCommand)
            blob_command = factory.create(BlobSampleCommand)
            ai_command = factory.create(AISampleCommand)
            plot_command = factory.create(CreatePlotCommand)

        # Assert
        assert isinstance(sample_command, SampleCommand)
        assert sample_command._telemetry_service is None
        assert sample_command._cache_service is None

        assert isinstance(blob_command, BlobSampleCommand)
        assert blob_command._blob_service is None

        assert isinstance(ai_command, AISampleCommand)
        assert ai_command._openai_service is None

        assert isinstance(plot_command, CreatePlotCommand)
        assert plot_command._blob_service is None

    def test_debug_logging(self, command_factory, capsys):
        """Test debug logging output."""
        # Act
        command = command_factory.create(SampleCommand)

        # Assert
        captured = capsys.readouterr()
        assert "CustomCommandInvokerFactory.create called for" in captured.out
        assert "SampleCommand" in captured.out
        assert "Blob service available: True" in captured.out
        assert "OpenAI service available: True" in captured.out
        assert "Cache service available: True" in captured.out
        assert "Telemetry service available: True" in captured.out
        assert "Creating SampleCommand" in captured.out

    def test_partial_services(self):
        """Test factory with partial services."""
        # Arrange
        factory = CustomCommandInvokerFactory(
            telemetry_service=MagicMock(),
            cache_service=None,
            blob_service=MagicMock(),
            openai_service=None
        )

        # Act
        with patch('builtins.print'):  # Suppress debug prints
            blob_command = factory.create(BlobSampleCommand)
            ai_command = factory.create(AISampleCommand)

        # Assert
        assert blob_command._telemetry_service is not None
        assert blob_command._blob_service is not None

        assert ai_command._telemetry_service is not None
        assert ai_command._cache_service is None
        assert ai_command._openai_service is None