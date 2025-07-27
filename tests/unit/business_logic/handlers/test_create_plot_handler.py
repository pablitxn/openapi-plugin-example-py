"""Unit tests for CreatePlotHandler."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from openapi_plugin_common import ValidationException
from src.openapi_plugin_example_py.business_logic.handlers.create_plot_handler import (
    CreatePlotHandler
)
from src.openapi_plugin_example_py.business_logic.commands.create_plot_command import (
    CreatePlotCommand,
    CreatePlotCommandContext,
    CreatePlotCommandResult
)
from src.openapi_plugin_example_py.business_logic.requests.create_plot_request import (
    CreatePlotRequest,
    CreatePlotResponse
)
from src.openapi_plugin_example_py.business_logic.options.plugin_options import (
    ExamplePluginOptions
)


class TestCreatePlotHandler:
    """Test suite for CreatePlotHandler."""

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
        return CreatePlotRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            excel_url="https://storage.azure.com/data/test.xlsx",
            plot_type="bar",
            x_column="Month",
            y_column="Sales",
            title="Monthly Sales",
            sheet_name="Sheet1",
            figure_size=(10, 6)
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
        handler = CreatePlotHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock the execute_command_async to populate context metadata
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = CreatePlotCommandResult(
                plot_url="https://storage.azure.com/plots/test-plot.png",
                file_name="test-plot.png",
                data_points=100
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        with patch('time.time', side_effect=[0, 0.2]):  # 200ms processing time
            response = await handler.execute_async(sample_request)

        # Assert
        assert isinstance(response, CreatePlotResponse)
        assert response.plot_url == "https://storage.azure.com/plots/test-plot.png"
        assert response.plot_type == "bar"
        assert response.file_name == "test-plot.png"
        assert response.processing_time_ms == 200.0
        assert response.data_points == 100

        # Verify command execution
        handler.execute_command_async.assert_called_once()
        call_args = handler.execute_command_async.call_args
        assert call_args[0][0] == CreatePlotCommand
        context = call_args[0][1]
        assert isinstance(context, CreatePlotCommandContext)
        assert context.excel_url == "https://storage.azure.com/data/test.xlsx"
        assert context.plot_type == "bar"
        assert context.x_column == "Month"
        assert context.y_column == "Sales"

    @pytest.mark.asyncio
    async def test_execute_async_no_excel_url(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution without Excel URL."""
        # Arrange
        request = CreatePlotRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            excel_url="",  # Empty URL
            plot_type="bar",
            x_column="Month",
            y_column="Sales"
        )
        
        handler = CreatePlotHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )

        # Act & Assert
        with pytest.raises(ValidationException, match="Excel URL is required"):
            await handler.execute_async(request)

    @pytest.mark.asyncio
    async def test_execute_async_missing_columns(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution with missing columns."""
        # Arrange - missing x_column
        request = CreatePlotRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            excel_url="https://storage.azure.com/data/test.xlsx",
            plot_type="bar",
            x_column="",  # Empty x_column
            y_column="Sales"
        )
        
        handler = CreatePlotHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )

        # Act & Assert
        with pytest.raises(ValidationException, match="Both x_column and y_column are required"):
            await handler.execute_async(request)

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
        handler = CreatePlotHandler(
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
        with pytest.raises(ValidationException, match="Command did not produce a result"):
            await handler.execute_async(sample_request)

    @pytest.mark.asyncio
    async def test_execute_async_with_optional_parameters(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution with optional parameters."""
        # Arrange - request without optional parameters
        request = CreatePlotRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            excel_url="https://storage.azure.com/data/test.xlsx",
            plot_type="line",
            x_column="Date",
            y_column="Value"
            # No title, sheet_name, or custom figure_size
        )
        
        handler = CreatePlotHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock result
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = CreatePlotCommandResult(
                plot_url="https://storage.azure.com/plots/line-plot.png",
                file_name="line-plot.png",
                data_points=50
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        response = await handler.execute_async(request)

        # Assert
        assert response.plot_type == "line"
        assert response.data_points == 50
        
        # Verify context creation with defaults
        call_args = handler.execute_command_async.call_args
        context = call_args[0][1]
        assert context.title is None
        assert context.sheet_name is None
        assert context.figure_size == (10, 6)  # Default value

    @pytest.mark.parametrize("plot_type", ["line", "bar", "scatter", "pie", "histogram", "box"])
    @pytest.mark.asyncio
    async def test_execute_async_different_plot_types(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service,
        plot_type
    ):
        """Test handler execution with different plot types."""
        # Arrange
        request = CreatePlotRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            excel_url="https://storage.azure.com/data/test.xlsx",
            plot_type=plot_type,
            x_column="X",
            y_column="Y"
        )
        
        handler = CreatePlotHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock result
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = CreatePlotCommandResult(
                plot_url=f"https://storage.azure.com/plots/{plot_type}-plot.png",
                file_name=f"{plot_type}-plot.png",
                data_points=25
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        response = await handler.execute_async(request)

        # Assert
        assert response.plot_type == plot_type
        assert response.plot_url == f"https://storage.azure.com/plots/{plot_type}-plot.png"

    @pytest.mark.asyncio
    async def test_execute_async_context_creation_details(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test detailed context creation from request."""
        # Arrange
        request = CreatePlotRequest(
            chat_id="unique-chat",
            agent_id="unique-agent",
            agent_version="3.0.0",
            excel_url="https://unique-url.com/data.xlsx",
            plot_type="scatter",
            x_column="UniqueX",
            y_column="UniqueY",
            title="Unique Title",
            sheet_name="UniqueSheet",
            figure_size=(12, 8)
        )
        
        handler = CreatePlotHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        captured_context = None
        
        async def capture_context(command_class, context):
            nonlocal captured_context
            captured_context = context
            context.metadata["result"] = CreatePlotCommandResult(
                plot_url="https://test.com/plot.png",
                file_name="plot.png",
                data_points=10
            )
        
        handler.execute_command_async = AsyncMock(side_effect=capture_context)

        # Act
        await handler.execute_async(request)

        # Assert
        assert captured_context is not None
        assert captured_context.chat_id == "unique-chat"
        assert captured_context.agent_id == "unique-agent"
        assert captured_context.agent_version == "3.0.0"
        assert captured_context.excel_url == "https://unique-url.com/data.xlsx"
        assert captured_context.plot_type == "scatter"
        assert captured_context.x_column == "UniqueX"
        assert captured_context.y_column == "UniqueY"
        assert captured_context.title == "Unique Title"
        assert captured_context.sheet_name == "UniqueSheet"
        assert captured_context.figure_size == (12, 8)