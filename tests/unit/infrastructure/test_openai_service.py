"""Unit tests for OpenAIService."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from openai import AsyncOpenAI

from src.openapi_plugin_example_py.infrastructure.openai.openai_service import OpenAIService


class TestOpenAIService:
    """Test suite for OpenAIService."""

    @pytest.fixture
    def mock_telemetry_service(self):
        """Create a mock telemetry service."""
        service = MagicMock()
        service.log_event = MagicMock()
        service.log_error = MagicMock()
        return service

    @pytest.fixture
    def mock_openai_response(self):
        """Create a mock OpenAI response."""
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "Generated response content"
        response.choices[0].finish_reason = "stop"
        response.model = "gpt-4"
        response.usage.prompt_tokens = 50
        response.usage.completion_tokens = 100
        response.usage.total_tokens = 150
        return response

    @pytest.fixture
    def openai_service(self, mock_telemetry_service):
        """Create an OpenAIService instance."""
        return OpenAIService(
            api_key="test-api-key",
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            telemetry_service=mock_telemetry_service
        )

    def test_initialization(self, mock_telemetry_service):
        """Test OpenAIService initialization."""
        # Act
        service = OpenAIService(
            api_key="test-key",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=500,
            telemetry_service=mock_telemetry_service
        )

        # Assert
        assert isinstance(service.client, AsyncOpenAI)
        assert service.model == "gpt-3.5-turbo"
        assert service.temperature == 0.5
        assert service.max_tokens == 500
        assert service.telemetry_service == mock_telemetry_service

    @pytest.mark.asyncio
    async def test_generate_completion_success(
        self, openai_service, mock_telemetry_service, mock_openai_response
    ):
        """Test successful completion generation."""
        # Arrange
        with patch.object(
            openai_service.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            return_value=mock_openai_response
        ) as mock_create:
            # Act
            result = await openai_service.generate_completion(
                system_prompt="You are a helpful assistant.",
                user_prompt="Hello, how are you?",
                chat_id="test-chat-123"
            )

            # Assert
            assert result["content"] == "Generated response content"
            assert result["model"] == "gpt-4"
            assert result["usage"]["total_tokens"] == 150
            assert result["finish_reason"] == "stop"

            # Verify API call
            mock_create.assert_called_once_with(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format=None
            )

            # Verify telemetry
            mock_telemetry_service.log_event.assert_called_once_with(
                "OpenAICompletionGenerated",
                {
                    "Model": "gpt-4",
                    "ChatId": "test-chat-123",
                    "PromptTokens": "50",
                    "CompletionTokens": "100",
                    "TotalTokens": "150"
                }
            )

    @pytest.mark.asyncio
    async def test_generate_completion_with_custom_parameters(
        self, openai_service, mock_openai_response
    ):
        """Test completion generation with custom parameters."""
        # Arrange
        with patch.object(
            openai_service.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            return_value=mock_openai_response
        ) as mock_create:
            # Act
            result = await openai_service.generate_completion(
                system_prompt="System prompt",
                user_prompt="User prompt",
                temperature=0.9,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            # Assert
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args["temperature"] == 0.9
            assert call_args["max_tokens"] == 2000
            assert call_args["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_generate_completion_exception_handling(
        self, openai_service, mock_telemetry_service
    ):
        """Test completion generation exception handling."""
        # Arrange
        error_message = "API rate limit exceeded"
        with patch.object(
            openai_service.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            side_effect=Exception(error_message)
        ):
            # Act & Assert
            with pytest.raises(Exception, match=error_message):
                await openai_service.generate_completion(
                    system_prompt="System",
                    user_prompt="User",
                    chat_id="test-chat"
                )

            # Verify error logging
            mock_telemetry_service.log_error.assert_called_once()
            call_args = mock_telemetry_service.log_error.call_args
            assert "OpenAI completion failed" in call_args[0][0]
            assert call_args[0][1]["Error"] == error_message
            assert call_args[0][1]["ChatId"] == "test-chat"

    @pytest.mark.asyncio
    async def test_generate_structured_output_success(
        self, openai_service, mock_telemetry_service
    ):
        """Test successful structured output generation."""
        # Arrange
        json_response = '{"name": "John", "age": 30}'
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json_response
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 60
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 80

        with patch.object(
            openai_service.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            # Act
            result = await openai_service.generate_structured_output(
                system_prompt="Generate user data",
                user_prompt="Create a user named John aged 30",
                json_schema='{"type": "object"}',
                chat_id="test-chat"
            )

            # Assert
            assert result == {"name": "John", "age": 30}

    @pytest.mark.asyncio
    async def test_generate_structured_output_invalid_json(
        self, openai_service, mock_telemetry_service
    ):
        """Test structured output generation with invalid JSON response."""
        # Arrange
        invalid_json = 'This is not valid JSON'
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = invalid_json
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 60
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 80

        with patch.object(
            openai_service.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid JSON response from OpenAI"):
                await openai_service.generate_structured_output(
                    system_prompt="Generate JSON",
                    user_prompt="Create invalid JSON",
                    json_schema='{"type": "object"}',
                    chat_id="test-chat"
                )

            # Verify error logging
            mock_telemetry_service.log_error.assert_called()
            call_args = mock_telemetry_service.log_error.call_args
            assert "Failed to parse OpenAI JSON response" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_generate_completion_without_telemetry(self, mock_openai_response):
        """Test completion generation without telemetry service."""
        # Arrange
        service = OpenAIService(
            api_key="test-api-key",
            model="gpt-4",
            telemetry_service=None
        )

        with patch.object(
            service.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            return_value=mock_openai_response
        ):
            # Act
            result = await service.generate_completion(
                system_prompt="System",
                user_prompt="User"
            )

            # Assert (should not raise any errors)
            assert result["content"] == "Generated response content"

    @pytest.mark.asyncio
    async def test_generate_completion_without_chat_id(
        self, openai_service, mock_telemetry_service, mock_openai_response
    ):
        """Test completion generation without chat ID."""
        # Arrange
        with patch.object(
            openai_service.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            return_value=mock_openai_response
        ):
            # Act
            result = await openai_service.generate_completion(
                system_prompt="System",
                user_prompt="User"
            )

            # Assert
            assert result["content"] == "Generated response content"
            
            # Verify telemetry uses empty string for chat ID
            mock_telemetry_service.log_event.assert_called_once()
            telemetry_props = mock_telemetry_service.log_event.call_args[0][1]
            assert telemetry_props["ChatId"] == ""

    def test_default_parameters(self):
        """Test default parameters when not specified."""
        # Act
        service = OpenAIService(api_key="test-key")

        # Assert
        assert service.model == "gpt-4"
        assert service.temperature == 0.7
        assert service.max_tokens == 1000
        assert service.telemetry_service is None