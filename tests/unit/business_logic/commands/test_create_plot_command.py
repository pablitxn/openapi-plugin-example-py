"""Unit tests for CreatePlotCommand."""
import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from openapi_plugin_common import (
    CommandException,
    ConfigurationException,
    ValidationException
)
from src.openapi_plugin_example_py.business_logic.commands.create_plot_command import (
    CreatePlotCommand,
    CreatePlotCommandContext,
    CreatePlotCommandResult
)


class TestCreatePlotCommand:
    """Test suite for CreatePlotCommand."""

    @pytest.fixture
    def mock_telemetry_service(self):
        """Create a mock telemetry service."""
        service = MagicMock()
        service.log_event = MagicMock()
        service.log_error = MagicMock()
        return service

    @pytest.fixture
    def mock_blob_service(self):
        """Create a mock blob service."""
        service = AsyncMock()
        service.download_blob_async = AsyncMock()
        service.upload_blob_async = AsyncMock(
            return_value="https://storage.azure.com/plots/test-plot.png"
        )
        return service

    @pytest.fixture
    def sample_context(self):
        """Create a sample command context."""
        context = CreatePlotCommandContext(
            excel_url="https://storage.azure.com/data/test.xlsx",
            plot_type="bar",
            x_column="Month",
            y_column="Sales",
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            title="Test Plot",
            sheet_name=None,
            figure_size=(10, 6),
            metadata={}
        )
        return context

    @pytest.fixture
    def sample_excel_data(self):
        """Create sample Excel data."""
        df = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
            'Sales': [100, 150, 200, 175, 250],
            'Costs': [50, 60, 70, 65, 80]
        })
        # Convert to Excel bytes
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sheet1', index=False)
        buffer.seek(0)
        return buffer.getvalue()

    @pytest.mark.asyncio
    async def test_execute_command_success(self, mock_telemetry_service, mock_blob_service, sample_context, sample_excel_data):
        """Test successful command execution."""
        # Arrange
        mock_blob_service.download_blob_async.return_value = sample_excel_data
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )

        # Act
        await command.execute_command_async(sample_context)

        # Assert
        assert "result" in sample_context.metadata
        result = sample_context.metadata["result"]
        assert isinstance(result, CreatePlotCommandResult)
        assert result.plot_url == "https://storage.azure.com/plots/test-plot.png"
        assert result.data_points == 5
        
        # Verify telemetry
        mock_telemetry_service.log_event.assert_called_once_with(
            "PlotCreated",
            {
                "ChatId": "test-chat-123",
                "PlotType": "bar",
                "DataPoints": "5",
                "Columns": "Month,Sales"
            }
        )

    @pytest.mark.asyncio
    async def test_execute_command_no_blob_service(self, mock_telemetry_service, sample_context):
        """Test command execution without blob service."""
        # Arrange
        command = CreatePlotCommand(telemetry_service=mock_telemetry_service)

        # Act & Assert
        with pytest.raises(ConfigurationException, match="Blob service is not configured"):
            await command.execute_command_async(sample_context)

    @pytest.mark.asyncio
    async def test_execute_command_invalid_plot_type(self, mock_telemetry_service, mock_blob_service, sample_context):
        """Test command execution with invalid plot type."""
        # Arrange
        sample_context.plot_type = "invalid_type"
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )

        # Act & Assert
        with pytest.raises(ValidationException, match="Invalid plot type"):
            await command.execute_command_async(sample_context)

    @pytest.mark.asyncio
    async def test_download_excel_from_file_url(self, mock_telemetry_service, mock_blob_service):
        """Test downloading Excel from file:// URL."""
        # Arrange
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )
        file_content = b"test excel content"
        
        with patch("builtins.open", mock_open(read_data=file_content)):
            # Act
            result = await command._download_excel_from_url("file:///tmp/test.xlsx")
            
            # Assert
            assert result == file_content

    @pytest.mark.asyncio
    async def test_download_excel_from_blob_url(self, mock_telemetry_service, mock_blob_service, sample_excel_data):
        """Test downloading Excel from blob storage URL."""
        # Arrange
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )
        mock_blob_service.download_blob_async.return_value = sample_excel_data

        # Act
        result = await command._download_excel_from_url(
            "https://storage.azure.com/data/test.xlsx"
        )

        # Assert
        assert result == sample_excel_data
        mock_blob_service.download_blob_async.assert_called_once_with(
            container_name="data",
            blob_name="test.xlsx"
        )

    @pytest.mark.asyncio
    async def test_download_excel_invalid_url(self, mock_telemetry_service, mock_blob_service):
        """Test downloading Excel with invalid URL."""
        # Arrange
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )

        # Act & Assert
        with pytest.raises(ValidationException, match="Invalid blob storage URL"):
            await command._download_excel_from_url("https://invalid-url")

    def test_read_excel_data_success(self, mock_telemetry_service, mock_blob_service, sample_excel_data):
        """Test successful Excel data reading."""
        # Arrange
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )

        # Act
        df = command._read_excel_data(sample_excel_data, None)

        # Assert
        assert len(df) == 5
        assert list(df.columns) == ['Month', 'Sales', 'Costs']

    def test_read_excel_data_with_sheet_name(self, mock_telemetry_service, mock_blob_service, sample_excel_data):
        """Test Excel data reading with specific sheet name."""
        # Arrange
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )

        # Act
        df = command._read_excel_data(sample_excel_data, "Sheet1")

        # Assert
        assert len(df) == 5

    def test_read_excel_data_invalid_data(self, mock_telemetry_service, mock_blob_service):
        """Test Excel data reading with invalid data."""
        # Arrange
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )

        # Act & Assert
        with pytest.raises(ValidationException, match="Failed to read Excel file"):
            command._read_excel_data(b"invalid excel data", None)

    def test_validate_columns_success(self, mock_telemetry_service, mock_blob_service):
        """Test successful column validation."""
        # Arrange
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        # Act & Assert (no exception should be raised)
        command._validate_columns(df, 'A', 'B')

    def test_validate_columns_missing_columns(self, mock_telemetry_service, mock_blob_service):
        """Test column validation with missing columns."""
        # Arrange
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        # Act & Assert
        with pytest.raises(ValidationException, match="Column\\(s\\) not found: C, D"):
            command._validate_columns(df, 'C', 'D')

    @pytest.mark.parametrize("plot_type", ['line', 'bar', 'scatter', 'pie', 'histogram', 'box'])
    def test_create_plot_various_types(self, mock_telemetry_service, mock_blob_service, plot_type):
        """Test plot creation for various plot types."""
        # Arrange
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )
        df = pd.DataFrame({
            'X': ['A', 'B', 'C', 'D', 'E'],
            'Y': [10, 20, 15, 25, 30]
        })

        # Act
        buffer = command._create_plot(
            df, plot_type, 'X', 'Y', "Test Plot", (10, 6)
        )

        # Assert
        assert isinstance(buffer, io.BytesIO)
        assert buffer.getvalue()[:8] == b'\x89PNG\r\n\x1a\n'  # PNG header

    def test_create_plot_with_default_title(self, mock_telemetry_service, mock_blob_service):
        """Test plot creation with default title."""
        # Arrange
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )
        df = pd.DataFrame({'X': [1, 2, 3], 'Y': [4, 5, 6]})

        # Act
        buffer = command._create_plot(
            df, 'line', 'X', 'Y', None, (10, 6)
        )

        # Assert
        assert isinstance(buffer, io.BytesIO)

    @pytest.mark.asyncio
    async def test_upload_plot_success(self, mock_telemetry_service, mock_blob_service):
        """Test successful plot upload."""
        # Arrange
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )
        plot_buffer = io.BytesIO(b"fake png data")

        # Act
        mock_uuid = MagicMock()
        mock_uuid.__str__ = MagicMock(return_value='12345678-1234-1234-1234-123456789012')
        with patch('uuid.uuid4', return_value=mock_uuid):
            with patch('src.openapi_plugin_example_py.business_logic.commands.create_plot_command.datetime') as mock_datetime:
                mock_datetime.utcnow.return_value.strftime.return_value = '20240101_120000'
                plot_url, file_name = await command._upload_plot(
                    plot_buffer, "test-chat", "bar"
                )

        # Assert
        assert plot_url == "https://storage.azure.com/plots/test-plot.png"
        assert file_name == "plot_bar_20240101_120000_12345678.png"
        
        # Verify upload call
        mock_blob_service.upload_blob_async.assert_called_once()
        call_args = mock_blob_service.upload_blob_async.call_args
        assert call_args[1]['container_name'] == 'plots'
        assert 'test-chat/plots/plot_bar_' in call_args[1]['blob_name']
        assert call_args[1]['content_type'] == 'image/png'

    @pytest.mark.asyncio
    async def test_execute_command_with_exception(self, mock_telemetry_service, mock_blob_service, sample_context):
        """Test command execution with exception handling."""
        # Arrange
        mock_blob_service.download_blob_async.side_effect = Exception("Download failed")
        command = CreatePlotCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )

        # Act & Assert
        with pytest.raises(CommandException, match="Failed to create plot"):
            await command.execute_command_async(sample_context)
        
        # Verify error logging
        mock_telemetry_service.log_error.assert_called_once()

    def test_create_plot_command_result_to_dict(self):
        """Test CreatePlotCommandResult to_dict method."""
        # Arrange
        result = CreatePlotCommandResult(
            plot_url="https://example.com/plot.png",
            file_name="plot.png",
            data_points=100
        )

        # Act
        result_dict = result.to_dict()

        # Assert
        assert result_dict == {
            "plotUrl": "https://example.com/plot.png",
            "fileName": "plot.png",
            "dataPoints": 100
        }