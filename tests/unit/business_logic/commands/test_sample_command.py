"""Unit tests for SampleCommand."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.openapi_plugin_example_py.business_logic.commands.sample_command import (
    SampleCommand,
    SampleCommandContext,
    SampleCommandResult
)


class TestSampleCommand:
    """Test suite for SampleCommand."""

    @pytest.fixture
    def mock_telemetry_service(self):
        """Create a mock telemetry service."""
        service = MagicMock()
        service.log_event = MagicMock()
        service.log_warning = MagicMock()
        return service

    @pytest.fixture
    def mock_cache_service(self):
        """Create a mock cache service."""
        service = AsyncMock()
        service.get = AsyncMock(return_value=None)
        service.set = AsyncMock()
        return service

    @pytest.fixture
    def sample_context(self):
        """Create a sample command context."""
        context = SampleCommandContext(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            sample_input="Hello World",
            use_cache=True
        )
        context.metadata = {}
        return context

    @pytest.mark.asyncio
    async def test_execute_command_without_cache(self, mock_telemetry_service):
        """Test command execution without cache."""
        # Arrange
        command = SampleCommand(telemetry_service=mock_telemetry_service)
        context = SampleCommandContext(
            chat_id="test-chat",
            agent_id="test-agent",
            agent_version="1.0.0",
            sample_input="test input",
            use_cache=False
        )
        context.metadata = {}

        # Act
        await command.execute_command_async(context)

        # Assert
        assert "result" in context.metadata
        result = context.metadata["result"]
        assert isinstance(result, SampleCommandResult)
        assert result.sample_response == "Processed: TEST INPUT"
        assert result.cached is False

    @pytest.mark.asyncio
    async def test_execute_command_with_cache_miss(self, mock_telemetry_service, mock_cache_service, sample_context):
        """Test command execution with cache miss."""
        # Arrange
        command = SampleCommand(
            telemetry_service=mock_telemetry_service,
            cache_service=mock_cache_service
        )

        # Act
        await command.execute_command_async(sample_context)

        # Assert
        assert "result" in sample_context.metadata
        result = sample_context.metadata["result"]
        assert result.sample_response == "Processed: HELLO WORLD"
        assert result.cached is False
        
        # Verify cache interactions
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command_with_cache_hit(self, mock_telemetry_service, mock_cache_service, sample_context):
        """Test command execution with cache hit."""
        # Arrange
        cached_value = "Cached: HELLO WORLD"
        mock_cache_service.get.return_value = cached_value
        
        command = SampleCommand(
            telemetry_service=mock_telemetry_service,
            cache_service=mock_cache_service
        )

        # Act
        await command.execute_command_async(sample_context)

        # Assert
        assert "result" in sample_context.metadata
        result = sample_context.metadata["result"]
        assert result.sample_response == cached_value
        assert result.cached is True
        
        # Verify cache get was called but set was not
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_sample_with_full_tracking(self, mock_telemetry_service):
        """Test sample processing with full tracking enabled."""
        # Arrange
        command = SampleCommand(telemetry_service=mock_telemetry_service)
        command._is_enabled_full_tracking = True

        # Act
        result = await command._process_sample("test")

        # Assert
        assert result == "Processed: TEST"
        mock_telemetry_service.log_event.assert_called_once_with(
            "SampleProcessed",
            {"InputLength": "4", "ProcessedLength": "15"}
        )

    @pytest.mark.asyncio
    async def test_get_from_cache_exception_handling(self, mock_telemetry_service, mock_cache_service):
        """Test cache get exception handling."""
        # Arrange
        mock_cache_service.get.side_effect = Exception("Cache error")
        command = SampleCommand(
            telemetry_service=mock_telemetry_service,
            cache_service=mock_cache_service
        )

        # Act
        result = await command._get_from_cache("test-key")

        # Assert
        assert result is None
        mock_telemetry_service.log_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_to_cache_exception_handling(self, mock_telemetry_service, mock_cache_service):
        """Test cache save exception handling."""
        # Arrange
        mock_cache_service.set.side_effect = Exception("Cache error")
        command = SampleCommand(
            telemetry_service=mock_telemetry_service,
            cache_service=mock_cache_service
        )

        # Act
        await command._save_to_cache("test-key", "test-value")

        # Assert
        mock_telemetry_service.log_warning.assert_called_once()

    def test_sample_command_result_to_dict(self):
        """Test SampleCommandResult to_dict method."""
        # Arrange
        result = SampleCommandResult(
            sample_response="Test response",
            cached=True
        )
        result.timestamp = "2024-01-01T00:00:00Z"

        # Act
        result_dict = result.to_dict()

        # Assert
        assert result_dict == {
            "sampleResponse": "Test response",
            "cached": True,
            "timestamp": "2024-01-01T00:00:00Z"
        }

    @pytest.mark.asyncio
    async def test_command_without_cache_service(self, mock_telemetry_service):
        """Test command execution without cache service."""
        # Arrange
        command = SampleCommand(telemetry_service=mock_telemetry_service)
        context = SampleCommandContext(
            chat_id="test-chat",
            agent_id="test-agent",
            agent_version="1.0.0",
            sample_input="no cache",
            use_cache=True  # Even with cache enabled
        )
        context.metadata = {}

        # Act
        await command.execute_command_async(context)

        # Assert
        assert "result" in context.metadata
        result = context.metadata["result"]
        assert result.sample_response == "Processed: NO CACHE"
        assert result.cached is False

    @pytest.mark.parametrize("input_text,expected_output", [
        ("hello", "Processed: HELLO"),
        ("Test Input", "Processed: TEST INPUT"),
        ("123", "Processed: 123"),
        ("", "Processed: "),
        ("   spaces   ", "Processed:    SPACES   ")
    ])
    @pytest.mark.asyncio
    async def test_process_sample_various_inputs(self, mock_telemetry_service, input_text, expected_output):
        """Test sample processing with various inputs."""
        # Arrange
        command = SampleCommand(telemetry_service=mock_telemetry_service)

        # Act
        result = await command._process_sample(input_text)

        # Assert
        assert result == expected_output