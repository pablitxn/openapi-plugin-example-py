"""Unit tests for AISampleCommand."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from openapi_plugin_common import (
    CommandException,
    ConfigurationException,
    ValidationException
)
from src.openapi_plugin_example_py.business_logic.commands.ai_sample_command import (
    AISampleCommand,
    AISampleCommandContext,
    AISampleCommandResult
)


class TestAISampleCommand:
    """Test suite for AISampleCommand."""

    @pytest.fixture
    def mock_telemetry_service(self):
        """Create a mock telemetry service."""
        service = MagicMock()
        service.log_event = MagicMock()
        service.log_error = MagicMock()
        return service

    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock OpenAI service."""
        service = AsyncMock()
        response = MagicMock()
        response.content = "AI generated response"
        response.model = "gpt-4"
        response.usage = {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150}
        service.generate_completion = AsyncMock(return_value=response)
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
        context = AISampleCommandContext(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Test prompt for AI"}
            ],
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            metadata={}
        )
        return context

    @pytest.mark.asyncio
    async def test_execute_command_with_ai_success(
        self, mock_telemetry_service, mock_llm_provider, mock_cache_service, sample_context
    ):
        """Test successful command execution with AI."""
        # Arrange
        command = AISampleCommand(
            telemetry_service=mock_telemetry_service,
            llm_provider=mock_llm_provider,
            cache_service=mock_cache_service
        )

        # Act
        await command.execute_command_async(sample_context)

        # Assert
        assert "result" in sample_context.metadata
        result = sample_context.metadata["result"]
        assert isinstance(result, AISampleCommandResult)
        assert result.ai_response == "AI generated response"
        assert result.model_used == "gpt-4"
        assert result.tokens_used == 150

        # Verify service calls
        mock_llm_provider.generate_completion.assert_called_once_with(
            system_prompt="You are a helpful AI assistant for processing sample requests.",
            user_prompt="Test prompt for AI",
            chat_id="test-chat-123"
        )
        mock_telemetry_service.log_event.assert_called_once()
        mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command_no_openai_service(self, mock_telemetry_service, sample_context):
        """Test command execution without LLM provider."""
        # Arrange
        command = AISampleCommand(telemetry_service=mock_telemetry_service)
        # AI is always used in the new version

        # Act & Assert
        with pytest.raises(ConfigurationException, match="LLM provider is not configured"):
            await command.execute_command_async(sample_context)

    @pytest.mark.asyncio
    async def test_execute_command_with_cache_hit(
        self, mock_telemetry_service, mock_llm_provider, mock_cache_service, sample_context
    ):
        """Test command execution with cache hit."""
        # Arrange
        cached_data = {
            "response": "Cached AI response",
            "model": "gpt-3.5",
            "tokens": 100
        }
        mock_cache_service.get.return_value = json.dumps(cached_data)
        
        command = AISampleCommand(
            telemetry_service=mock_telemetry_service,
            llm_provider=mock_llm_provider,
            cache_service=mock_cache_service
        )

        # Act
        await command.execute_command_async(sample_context)

        # Assert
        assert "result" in sample_context.metadata
        result = sample_context.metadata["result"]
        assert result.ai_response == "Cached AI response"
        assert result.model_used == "gpt-3.5"
        assert result.tokens_used == 100

        # Verify OpenAI was not called due to cache hit
        mock_llm_provider.generate_completion.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_command_without_ai(
        self, mock_telemetry_service, mock_cache_service, sample_context
    ):
        """Test command execution without AI (fallback mode)."""
        # Arrange
        # Testing without AI (fallback mode)
        command = AISampleCommand(
            telemetry_service=mock_telemetry_service,
            cache_service=mock_cache_service
        )

        # Act
        await command.execute_command_async(sample_context)

        # Assert
        assert "result" in sample_context.metadata
        result = sample_context.metadata["result"]
        assert result.ai_response == "Fallback response for: Test prompt for AI"
        assert result.model_used == "fallback"
        assert result.tokens_used == 0

    @pytest.mark.asyncio
    async def test_process_with_ai_validation_failure(
        self, mock_telemetry_service, mock_llm_provider, sample_context
    ):
        """Test AI processing with schema validation failure."""
        # Arrange
        response = MagicMock()
        # Missing 'content' attribute
        response.content = None
        response.model = "gpt-4"
        response.usage = {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150}
        mock_llm_provider.generate_completion.return_value = response
        
        command = AISampleCommand(
            telemetry_service=mock_telemetry_service,
            llm_provider=mock_llm_provider
        )

        # Act & Assert
        with pytest.raises(CommandException, match="AI processing failed"):
            await command._process_with_ai(sample_context)

    @pytest.mark.asyncio
    async def test_process_with_ai_exception_handling(
        self, mock_telemetry_service, mock_llm_provider, sample_context
    ):
        """Test AI processing exception handling."""
        # Arrange
        mock_llm_provider.generate_completion.side_effect = Exception("OpenAI API error")
        
        command = AISampleCommand(
            telemetry_service=mock_telemetry_service,
            llm_provider=mock_llm_provider
        )

        # Act & Assert
        with pytest.raises(CommandException, match="AI processing failed"):
            await command._process_with_ai(sample_context)
        
        # Verify error logging
        mock_telemetry_service.log_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_without_ai(self, mock_telemetry_service):
        """Test processing without AI."""
        # Arrange
        command = AISampleCommand(telemetry_service=mock_telemetry_service)

        # Act
        messages = [{"role": "user", "content": "Test prompt"}]
        result = await command._process_without_ai(messages)

        # Assert
        assert result.content == "Fallback response for: Test prompt"
        assert result.model == "fallback"
        assert result.total_tokens > 0

    def test_validate_response_schema_success(self, mock_telemetry_service):
        """Test successful response schema validation."""
        # Arrange
        command = AISampleCommand(telemetry_service=mock_telemetry_service)
        response = MagicMock()
        response.content = "Valid response"

        # Act & Assert (no exception should be raised)
        command._validate_response_schema(response)

    def test_validate_response_schema_failure(self, mock_telemetry_service):
        """Test response schema validation failure."""
        # Arrange
        command = AISampleCommand(telemetry_service=mock_telemetry_service)
        response = MagicMock()
        # Missing content attribute
        del response.content

        # Act & Assert
        with pytest.raises(ValidationException, match="AI response missing 'content' field"):
            command._validate_response_schema(response)

    @pytest.mark.asyncio
    async def test_get_from_cache_with_json_string(self, mock_telemetry_service, mock_cache_service):
        """Test getting JSON string from cache."""
        # Arrange
        cached_data = {"key": "value"}
        mock_cache_service.get.return_value = json.dumps(cached_data)
        
        command = AISampleCommand(
            telemetry_service=mock_telemetry_service,
            cache_service=mock_cache_service
        )

        # Act
        result = await command._get_from_cache("test-key")

        # Assert
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_get_from_cache_with_dict(self, mock_telemetry_service, mock_cache_service):
        """Test getting dict from cache."""
        # Arrange
        cached_data = {"key": "value"}
        mock_cache_service.get.return_value = cached_data
        
        command = AISampleCommand(
            telemetry_service=mock_telemetry_service,
            cache_service=mock_cache_service
        )

        # Act
        result = await command._get_from_cache("test-key")

        # Assert
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_get_from_cache_exception(self, mock_telemetry_service, mock_cache_service):
        """Test cache get with exception."""
        # Arrange
        mock_cache_service.get.side_effect = Exception("Cache error")
        
        command = AISampleCommand(
            telemetry_service=mock_telemetry_service,
            cache_service=mock_cache_service
        )

        # Act
        result = await command._get_from_cache("test-key")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_save_to_cache_success(self, mock_telemetry_service, mock_cache_service):
        """Test successful cache save."""
        # Arrange
        command = AISampleCommand(
            telemetry_service=mock_telemetry_service,
            cache_service=mock_cache_service
        )
        data = {"key": "value"}

        # Act
        await command._save_to_cache("test-key", data)

        # Assert
        mock_cache_service.set.assert_called_once_with(
            "test-key",
            json.dumps(data),
            expire=3600
        )

    @pytest.mark.asyncio
    async def test_save_to_cache_exception(self, mock_telemetry_service, mock_cache_service):
        """Test cache save with exception."""
        # Arrange
        mock_cache_service.set.side_effect = Exception("Cache error")
        
        command = AISampleCommand(
            telemetry_service=mock_telemetry_service,
            cache_service=mock_cache_service
        )

        # Act (should not raise exception)
        await command._save_to_cache("test-key", {"data": "value"})

        # Assert
        mock_cache_service.set.assert_called_once()

    def test_ai_sample_command_result_to_dict(self):
        """Test AISampleCommandResult to_dict method."""
        # Arrange
        result = AISampleCommandResult(
            id="chatcmpl-test",
            model="gpt-4",
            content="Test response",
            finish_reason="stop",
            prompt_tokens=25,
            completion_tokens=75,
            total_tokens=100
        )

        # Assert attributes directly
        assert result.id == "chatcmpl-test"
        assert result.model == "gpt-4"
        assert result.content == "Test response"
        assert result.finish_reason == "stop"
        assert result.prompt_tokens == 25
        assert result.completion_tokens == 75
        assert result.total_tokens == 100
        assert result.created > 0

    @pytest.mark.asyncio
    async def test_execute_command_no_validation(
        self, mock_telemetry_service, mock_llm_provider, mock_cache_service, sample_context
    ):
        """Test command execution without schema validation."""
        # Arrange
        # Schema validation removed in new version
        response = MagicMock()
        # Even with missing content, no validation should allow it
        response.content = ""
        response.model = "gpt-4"
        response.usage = {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150}
        mock_llm_provider.generate_completion.return_value = response
        
        command = AISampleCommand(
            telemetry_service=mock_telemetry_service,
            llm_provider=mock_llm_provider,
            cache_service=mock_cache_service
        )

        # Act
        await command.execute_command_async(sample_context)

        # Assert
        assert "result" in sample_context.metadata
        result = sample_context.metadata["result"]
        assert result.ai_response == ""  # Empty due to missing content field
        assert result.model_used == "gpt-4"