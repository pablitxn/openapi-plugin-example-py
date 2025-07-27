"""Unit tests for AISampleHandler."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.openapi_plugin_example_py.business_logic.handlers.ai_sample_handler import (
    AISampleHandler
)
from src.openapi_plugin_example_py.business_logic.commands.ai_sample_command import (
    AISampleCommand,
    AISampleCommandContext,
    AISampleCommandResult
)
from src.openapi_plugin_example_py.business_logic.requests.ai_sample_request import (
    AISampleRequest,
    AISampleResponse
)
from src.openapi_plugin_example_py.business_logic.options.plugin_options import (
    ExamplePluginOptions
)
from openapi_plugin_common import OpenAIConfig


class TestAISampleHandler:
    """Test suite for AISampleHandler."""

    @pytest.fixture
    def mock_command_invoker_factory(self):
        """Create a mock command invoker factory."""
        factory = MagicMock()
        invoker = AsyncMock()
        factory.create_command_invoker.return_value = invoker
        return factory

    @pytest.fixture
    def plugin_options(self):
        """Create plugin options with OpenAI settings."""
        from openapi_plugin_common import SchemasConfig
        
        options = ExamplePluginOptions(
            schemas=SchemasConfig(
                sample='{}',
                ai_sample='{}'
            )
        )
        options.openai = OpenAIConfig(api_key="test-key")
        options.openai.temperature = 0.7
        options.openai.max_tokens = 1000
        return options

    @pytest.fixture
    def mock_telemetry_service(self):
        """Create a mock telemetry service."""
        service = MagicMock()
        return service

    @pytest.fixture
    def sample_request(self):
        """Create a sample request."""
        return AISampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Generate a test response"}
            ],
            temperature=None,
            max_tokens=None
        )

    @pytest.mark.asyncio
    async def test_handle_async_success(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service,
        sample_request
    ):
        """Test successful handler execution."""
        # Arrange
        handler = AISampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock the execute_command_async to populate context metadata
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = AISampleCommandResult(
                id="chatcmpl-test123",
                model="gpt-4",
                content="Generated AI response",
                finish_reason="stop",
                prompt_tokens=50,
                completion_tokens=100,
                total_tokens=150
            )
            context.metadata["cached"] = False
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        response = await handler.handle_async(sample_request)

        # Assert
        assert isinstance(response, AISampleResponse)
        assert response.id.startswith("chatcmpl-")
        assert response.object == "chat.completion"
        assert response.model == "gpt-4"
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Generated AI response"
        assert response.choices[0].message.role == "assistant"
        assert response.usage.total_tokens == 150
        assert response.cached is False

        # Verify command execution
        handler.execute_command_async.assert_called_once()
        call_args = handler.execute_command_async.call_args
        assert call_args[0][0] == AISampleCommand
        context = call_args[0][1]
        assert isinstance(context, AISampleCommandContext)
        assert context.sample_prompt == "Generate a test response"
        assert context.use_ai is True
        assert context.validate_schema is True

    @pytest.mark.asyncio
    async def test_handle_async_with_custom_temperature(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution with custom temperature."""
        # Arrange
        request = AISampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            messages=[
                {"role": "user", "content": "Test prompt"}
            ],
            temperature=0.9,
            max_tokens=500
        )
        
        handler = AISampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock result
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = AISampleCommandResult(
                id="chatcmpl-test456",
                model="gpt-4",
                content="Response",
                finish_reason="stop",
                prompt_tokens=20,
                completion_tokens=80,
                total_tokens=100
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        await handler.handle_async(request)

        # Assert
        assert plugin_options.openai.temperature == 0.9
        assert plugin_options.openai.max_tokens == 500

    @pytest.mark.asyncio
    async def test_handle_async_without_ai(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution without AI."""
        # Arrange
        request = AISampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            messages=[
                {"role": "user", "content": "Test prompt"}
            ]
        )
        
        handler = AISampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock fallback result
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = AISampleCommandResult(
                id="chatcmpl-fallback",
                model="fallback",
                content="Fallback response",
                finish_reason="stop",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        response = await handler.handle_async(request)

        # Assert
        assert response.id.startswith("chatcmpl-")
        assert response.model == "fallback"
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Fallback response"
        assert response.usage.total_tokens == 0

    @pytest.mark.asyncio
    async def test_handle_async_cached_result(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service,
        sample_request
    ):
        """Test handler execution with cached result."""
        # Arrange
        handler = AISampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock cached result
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = AISampleCommandResult(
                id="chatcmpl-cached",
                model="gpt-3.5",
                content="Cached AI response",
                finish_reason="stop",
                prompt_tokens=30,
                completion_tokens=50,
                total_tokens=80
            )
            context.metadata["cached"] = True
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        response = await handler.handle_async(sample_request)

        # Assert
        assert response.id.startswith("chatcmpl-")
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Cached AI response"
        assert response.cached is True

    @pytest.mark.asyncio
    async def test_handle_async_no_result_error(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service,
        sample_request
    ):
        """Test handler execution when command doesn't produce result."""
        # Arrange
        handler = AISampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock command execution without result
        async def mock_execute_command(command_class, context):
            # Don't set any result in metadata
            pass
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act & Assert
        with pytest.raises(ValueError, match="Command did not produce a result"):
            await handler.handle_async(sample_request)

    @pytest.mark.asyncio
    async def test_handle_async_no_openai_options(
        self,
        mock_command_invoker_factory,
        mock_telemetry_service,
        sample_request
    ):
        """Test handler execution without OpenAI options."""
        # Arrange
        from openapi_plugin_common import SchemasConfig
        options = ExamplePluginOptions(
            schemas=SchemasConfig(
                sample='{}',
                ai_sample='{}'
            )
        )
        options.openai = None  # No OpenAI options
        
        request = AISampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            sample_prompt="Test",
            use_ai=True,
            validate_schema=True,
            temperature=0.8,  # Should not cause error
            max_tokens=200
        )
        
        handler = AISampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock result
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = AISampleCommandResult(
                id="chatcmpl-test789",
                model="gpt-4",
                content="Response",
                finish_reason="stop",
                prompt_tokens=20,
                completion_tokens=30,
                total_tokens=50
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act (should not raise exception)
        response = await handler.handle_async(request)

        # Assert
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Response"

    @pytest.mark.asyncio
    async def test_handle_async_context_creation_details(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test detailed context creation from request."""
        # Arrange
        request = AISampleRequest(
            chat_id="unique-chat",
            agent_id="unique-agent",
            agent_version="2.5.0",
            messages=[
                {"role": "user", "content": "Unique prompt for testing"}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        
        handler = AISampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        captured_context = None
        
        async def capture_context(command_class, context):
            nonlocal captured_context
            captured_context = context
            context.metadata["result"] = AISampleCommandResult(
                id="chatcmpl-testcontext",
                model="test",
                content="Test",
                finish_reason="stop",
                prompt_tokens=5,
                completion_tokens=5,
                total_tokens=10
            )
        
        handler.execute_command_async = AsyncMock(side_effect=capture_context)

        # Act
        await handler.handle_async(request)

        # Assert
        assert captured_context is not None
        assert captured_context.chat_id == "unique-chat"
        assert captured_context.agent_id == "unique-agent"
        assert captured_context.agent_version == "2.5.0"
        assert captured_context.sample_prompt == "Unique prompt for testing"
        assert captured_context.use_ai is False
        assert captured_context.validate_schema is False
        
        # Also verify options were updated
        assert plugin_options.openai.temperature == 0.5
        assert plugin_options.openai.max_tokens == 1500