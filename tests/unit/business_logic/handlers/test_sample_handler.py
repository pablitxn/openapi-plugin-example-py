"""Unit tests for SampleHandler."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from src.openapi_plugin_example_py.business_logic.handlers.sample_handler import (
    SampleHandler
)
from src.openapi_plugin_example_py.business_logic.commands.sample_command import (
    SampleCommand,
    SampleCommandContext,
    SampleCommandResult
)
from src.openapi_plugin_example_py.business_logic.requests.sample_request import (
    SampleRequest,
    SampleResponse
)
from src.openapi_plugin_example_py.business_logic.options.plugin_options import (
    ExamplePluginOptions
)


class TestSampleHandler:
    """Test suite for SampleHandler."""

    @pytest.fixture
    def mock_command_invoker_factory(self):
        """Create a mock command invoker factory."""
        factory = MagicMock()
        invoker = AsyncMock()
        factory.create_command_invoker.return_value = invoker
        return factory

    @pytest.fixture
    def plugin_options(self):
        """Create plugin options."""
        return ExamplePluginOptions()

    @pytest.fixture
    def mock_telemetry_service(self):
        """Create a mock telemetry service."""
        service = MagicMock()
        return service

    @pytest.fixture
    def sample_request(self):
        """Create a sample request."""
        return SampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            sample_input="Test input",
            use_cache=True
        )

    @pytest.mark.asyncio
    async def test_execute_async_success(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service,
        sample_request
    ):
        """Test successful handler execution."""
        # Arrange
        handler = SampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock the execute_command_async to populate context metadata
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = SampleCommandResult(
                sample_response="Processed: TEST INPUT",
                cached=False
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        with patch('time.time', side_effect=[0, 0.1]):  # 100ms processing time
            response = await handler.execute_async(sample_request)

        # Assert
        assert isinstance(response, SampleResponse)
        assert response.sample_response == "Processed: TEST INPUT"
        assert response.cached is False
        assert response.processing_time_ms == 100.0

        # Verify command execution
        handler.execute_command_async.assert_called_once()
        call_args = handler.execute_command_async.call_args
        assert call_args[0][0] == SampleCommand
        context = call_args[0][1]
        assert isinstance(context, SampleCommandContext)
        assert context.chat_id == "test-chat-123"
        assert context.sample_input == "Test input"
        assert context.use_cache is True

    @pytest.mark.asyncio
    async def test_execute_async_cached_result(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service,
        sample_request
    ):
        """Test handler execution with cached result."""
        # Arrange
        handler = SampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock cached result
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = SampleCommandResult(
                sample_response="Cached result",
                cached=True
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        response = await handler.execute_async(sample_request)

        # Assert
        assert response.sample_response == "Cached result"
        assert response.cached is True

    @pytest.mark.asyncio
    async def test_execute_async_no_cache(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution without cache."""
        # Arrange
        request = SampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            sample_input="Test input",
            use_cache=False
        )
        
        handler = SampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock result
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = SampleCommandResult(
                sample_response="Fresh result",
                cached=False
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        response = await handler.execute_async(request)

        # Assert
        assert response.sample_response == "Fresh result"
        assert response.cached is False
        
        # Verify context was created with use_cache=False
        call_args = handler.execute_command_async.call_args
        context = call_args[0][1]
        assert context.use_cache is False

    @pytest.mark.asyncio
    async def test_execute_async_no_result_error(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service,
        sample_request
    ):
        """Test handler execution when command doesn't produce result."""
        # Arrange
        handler = SampleHandler(
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
            await handler.execute_async(sample_request)

    @pytest.mark.asyncio
    async def test_execute_async_processing_time_calculation(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service,
        sample_request
    ):
        """Test processing time calculation."""
        # Arrange
        handler = SampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock result
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = SampleCommandResult(
                sample_response="Result",
                cached=False
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act with specific time values
        with patch('time.time', side_effect=[1000.0, 1000.25]):  # 250ms
            response = await handler.execute_async(sample_request)

        # Assert
        assert response.processing_time_ms == 250.0

    @pytest.mark.asyncio
    async def test_handler_initialization(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler initialization."""
        # Act
        handler = SampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )

        # Assert
        assert handler._command_invoker_factory == mock_command_invoker_factory
        assert handler._plugin_options == plugin_options
        assert handler._telemetry_service == mock_telemetry_service

    @pytest.mark.asyncio
    async def test_execute_async_context_creation(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test proper context creation from request."""
        # Arrange
        request = SampleRequest(
            chat_id="unique-chat-id",
            agent_id="unique-agent",
            agent_version="2.0.0",
            sample_input="Unique input",
            use_cache=False
        )
        
        handler = SampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        captured_context = None
        
        async def capture_context(command_class, context):
            nonlocal captured_context
            captured_context = context
            context.metadata["result"] = SampleCommandResult(
                sample_response="Result",
                cached=False
            )
        
        handler.execute_command_async = AsyncMock(side_effect=capture_context)

        # Act
        await handler.execute_async(request)

        # Assert
        assert captured_context is not None
        assert captured_context.chat_id == "unique-chat-id"
        assert captured_context.agent_id == "unique-agent"
        assert captured_context.agent_version == "2.0.0"
        assert captured_context.sample_input == "Unique input"
        assert captured_context.use_cache is False