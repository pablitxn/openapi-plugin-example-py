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
            'llm_provider': MagicMock(name='llm_provider')
        }

    @pytest.fixture
    def command_factory(self, mock_services):
        """Create a CustomCommandInvokerFactory instance."""
        return CustomCommandInvokerFactory(
            telemetry_service=mock_services['telemetry_service'],
            cache_service=mock_services['cache_service'],
            blob_service=mock_services['blob_service'],
            llm_provider=mock_services['llm_provider']
        )

    def test_initialization(self, mock_services):
        """Test factory initialization."""
        # Act
        factory = CustomCommandInvokerFactory(
            telemetry_service=mock_services['telemetry_service'],
            cache_service=mock_services['cache_service'],
            blob_service=mock_services['blob_service'],
            llm_provider=mock_services['llm_provider']
        )

        # Assert
        assert factory._telemetry_service == mock_services['telemetry_service']
        assert factory._cache_service == mock_services['cache_service']
        assert factory._blob_service == mock_services['blob_service']
        assert factory._llm_provider == mock_services['llm_provider']

    def test_create_sample_command(self, command_factory, mock_services):
        """Test creating SampleCommand."""
        # Act
        with patch('builtins.print'):  # Suppress debug prints
            command = command_factory.create(SampleCommand)

        # Assert
        from openapi_plugin_common.log_events import LoggedCommandWrapper
        assert isinstance(command, LoggedCommandWrapper)
        assert isinstance(command.command, SampleCommand)
        assert command.command._telemetry_service == mock_services['telemetry_service']
        assert command.command._cache_service == mock_services['cache_service']

    def test_create_blob_sample_command(self, command_factory, mock_services):
        """Test creating BlobSampleCommand."""
        # Act
        with patch('builtins.print'):  # Suppress debug prints
            command = command_factory.create(BlobSampleCommand)

        # Assert
        from openapi_plugin_common.log_events import LoggedCommandWrapper
        assert isinstance(command, LoggedCommandWrapper)
        assert isinstance(command.command, BlobSampleCommand)
        assert command.command._telemetry_service == mock_services['telemetry_service']
        assert command.command._blob_service == mock_services['blob_service']

    def test_create_ai_sample_command(self, command_factory, mock_services):
        """Test creating AISampleCommand."""
        # Act
        with patch('builtins.print'):  # Suppress debug prints
            command = command_factory.create(AISampleCommand)

        # Assert
        from openapi_plugin_common.log_events import LoggedCommandWrapper
        assert isinstance(command, LoggedCommandWrapper)
        assert isinstance(command.command, AISampleCommand)
        assert command.command._telemetry_service == mock_services['telemetry_service']
        assert command.command._cache_service == mock_services['cache_service']
        assert command.command._llm_provider == mock_services['llm_provider']

    def test_create_create_plot_command(self, command_factory, mock_services):
        """Test creating CreatePlotCommand."""
        # Act
        with patch('builtins.print'):  # Suppress debug prints
            command = command_factory.create(CreatePlotCommand)

        # Assert
        from openapi_plugin_common.log_events import LoggedCommandWrapper
        assert isinstance(command, LoggedCommandWrapper)
        assert isinstance(command.command, CreatePlotCommand)
        assert command.command._telemetry_service == mock_services['telemetry_service']
        assert command.command._blob_service == mock_services['blob_service']

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
        from openapi_plugin_common.log_events import LoggedCommandWrapper
        assert isinstance(command, LoggedCommandWrapper)
        assert isinstance(command.command, UnknownCommand)
        mock_parent_create.assert_called_once_with(UnknownCommand)

    def test_create_with_none_services(self):
        """Test factory works with None services."""
        # Arrange
        factory = CustomCommandInvokerFactory(
            telemetry_service=None,
            cache_service=None,
            blob_service=None,
            llm_provider=None
        )

        # Act
        with patch('builtins.print'):  # Suppress debug prints
            sample_command = factory.create(SampleCommand)
            blob_command = factory.create(BlobSampleCommand)
            ai_command = factory.create(AISampleCommand)
            plot_command = factory.create(CreatePlotCommand)

        # Assert
        from openapi_plugin_common.log_events import LoggedCommandWrapper
        assert isinstance(sample_command, LoggedCommandWrapper)
        assert isinstance(sample_command.command, SampleCommand)
        # When telemetry_service is None, CommandBase initializes with NoOpTelemetry
        from openapi_plugin_common.telemetry import NoOpTelemetry
        assert isinstance(sample_command.command._telemetry_service, NoOpTelemetry)
        assert sample_command.command._cache_service is None

        assert isinstance(blob_command, LoggedCommandWrapper)
        assert isinstance(blob_command.command, BlobSampleCommand)
        assert blob_command.command._blob_service is None

        assert isinstance(ai_command, LoggedCommandWrapper)
        assert isinstance(ai_command.command, AISampleCommand)
        assert ai_command.command._llm_provider is None

        assert isinstance(plot_command, LoggedCommandWrapper)
        assert isinstance(plot_command.command, CreatePlotCommand)
        assert plot_command.command._blob_service is None

    def test_debug_logging(self, command_factory, capsys):
        """Test debug logging output."""
        # Act
        command = command_factory.create(SampleCommand)

        # Assert
        captured = capsys.readouterr()
        assert "CustomCommandInvokerFactory.create called for" in captured.out
        assert "SampleCommand" in captured.out
        assert "Blob service available: True" in captured.out
        assert "LLM provider available: True" in captured.out
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
            llm_provider=None
        )

        # Act
        with patch('builtins.print'):  # Suppress debug prints
            blob_command = factory.create(BlobSampleCommand)
            ai_command = factory.create(AISampleCommand)

        # Assert
        from openapi_plugin_common.log_events import LoggedCommandWrapper
        assert isinstance(blob_command, LoggedCommandWrapper)
        assert blob_command.command._telemetry_service is not None
        assert blob_command.command._blob_service is not None

        assert isinstance(ai_command, LoggedCommandWrapper)
        assert ai_command.command._telemetry_service is not None
        assert ai_command.command._cache_service is None
        assert ai_command.command._llm_provider is None