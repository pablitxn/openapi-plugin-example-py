"""Unit tests for BlobSampleCommand."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from openapi_plugin_common import (
    CommandException,
    ConfigurationException,
    ValidationException,
    SupportedFileType
)
from src.openapi_plugin_example_py.business_logic.commands.blob_sample_command import (
    BlobSampleCommand,
    BlobSampleCommandContext,
    BlobSampleCommandResult
)


class TestBlobSampleCommand:
    """Test suite for BlobSampleCommand."""

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
        service.upload_blob_async = AsyncMock(
            return_value="https://storage.azure.com/dev-uploads/test-file.pdf"
        )
        return service

    @pytest.fixture
    def sample_context(self):
        """Create a sample command context."""
        context = BlobSampleCommandContext(
            file_name="test-document.pdf",
            file_content=b"PDF content here",
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            container_name=None,
            metadata={}
        )
        return context

    @pytest.mark.asyncio
    async def test_execute_command_success(
        self, mock_telemetry_service, mock_blob_service, sample_context
    ):
        """Test successful command execution."""
        # Arrange
        command = BlobSampleCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )

        # Act
        mock_uuid = MagicMock()
        mock_uuid.__str__ = MagicMock(return_value='12345678-1234-1234-1234-123456789012')
        with patch('uuid.uuid4', return_value=mock_uuid):
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
                await command.execute_command_async(sample_context)

        # Assert
        assert "result" in sample_context.metadata
        result = sample_context.metadata["result"]
        assert isinstance(result, BlobSampleCommandResult)
        assert result.blob_url == "https://storage.azure.com/dev-uploads/test-file.pdf"
        assert result.file_size == len(sample_context.file_content)
        assert result.operation == "upload"

        # Verify telemetry
        mock_telemetry_service.log_event.assert_called_once_with(
            "BlobUploaded",
            {
                "ChatId": "test-chat-123",
                "FileName": "test-document.pdf",
                "FileSize": "16",
                "FileType": "pdf",
                "Container": "default"
            }
        )

    @pytest.mark.asyncio
    async def test_execute_command_no_blob_service(self, mock_telemetry_service, sample_context):
        """Test command execution without blob service."""
        # Arrange
        command = BlobSampleCommand(telemetry_service=mock_telemetry_service)

        # Act & Assert
        with pytest.raises(ConfigurationException, match="Blob service is not configured"):
            await command.execute_command_async(sample_context)

    @pytest.mark.asyncio
    async def test_execute_command_file_too_large(
        self, mock_telemetry_service, mock_blob_service, sample_context
    ):
        """Test command execution with file too large."""
        # Arrange
        command = BlobSampleCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )
        command._options = {"max_file_size_mb": 0.00001}  # Very small limit
        sample_context.file_content = b"x" * 1000  # Larger than limit

        # Act & Assert
        with pytest.raises(ValidationException, match="File size exceeds maximum allowed size"):
            await command.execute_command_async(sample_context)

    @pytest.mark.asyncio
    async def test_upload_blob_success(
        self, mock_telemetry_service, mock_blob_service, sample_context
    ):
        """Test successful blob upload."""
        # Arrange
        command = BlobSampleCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )
        file_type = SupportedFileType.PDF

        # Act
        mock_uuid = MagicMock()
        mock_uuid.__str__ = MagicMock(return_value='12345678-1234-1234-1234-123456789012')
        with patch('uuid.uuid4', return_value=mock_uuid):
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
                result = await command._upload_blob(sample_context, file_type)

        # Assert
        assert result.blob_url == "https://storage.azure.com/dev-uploads/test-file.pdf"
        assert result.file_size == 16
        assert result.operation == "upload"

        # Verify blob service call
        mock_blob_service.upload_blob_async.assert_called_once()
        call_args = mock_blob_service.upload_blob_async.call_args
        assert call_args[1]['container_name'] == 'dev-uploads'
        assert 'test-chat-123/20240101_120000_12345678_test-document.pdf' in call_args[1]['blob_name']
        assert call_args[1]['content_type'] == 'application/pdf'

    @pytest.mark.asyncio
    async def test_upload_blob_with_custom_container(
        self, mock_telemetry_service, mock_blob_service, sample_context
    ):
        """Test blob upload with custom container."""
        # Arrange
        sample_context.container_name = "custom-container"
        command = BlobSampleCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )
        file_type = SupportedFileType.PDF

        # Act
        result = await command._upload_blob(sample_context, file_type)

        # Assert
        mock_blob_service.upload_blob_async.assert_called_once()
        call_args = mock_blob_service.upload_blob_async.call_args
        assert call_args[1]['container_name'] == 'custom-container'

    @pytest.mark.asyncio
    async def test_upload_blob_exception_handling(
        self, mock_telemetry_service, mock_blob_service, sample_context
    ):
        """Test blob upload exception handling."""
        # Arrange
        mock_blob_service.upload_blob_async.side_effect = Exception("Upload failed")
        command = BlobSampleCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )
        file_type = SupportedFileType.PDF

        # Act & Assert
        with pytest.raises(CommandException, match="Failed to upload blob"):
            await command._upload_blob(sample_context, file_type)

        # Verify error logging
        mock_telemetry_service.log_error.assert_called_once()

    @pytest.mark.parametrize("file_name,expected_type", [
        ("document.pdf", SupportedFileType.PDF),
        ("image.png", SupportedFileType.PNG),
        ("photo.jpg", SupportedFileType.JPG),
        ("photo.jpeg", SupportedFileType.JPEG),
        ("text.txt", SupportedFileType.TXT),
        ("data.json", SupportedFileType.JSON),
        ("data.csv", SupportedFileType.CSV),
        ("spreadsheet.xlsx", SupportedFileType.XLSX),
        ("spreadsheet.xls", SupportedFileType.XLS),
        ("document.docx", SupportedFileType.DOCX),
        ("document.doc", SupportedFileType.DOC),
        ("presentation.pptx", SupportedFileType.OTHER),
        ("presentation.ppt", SupportedFileType.OTHER),
        ("archive.zip", SupportedFileType.ZIP),
        ("unknown.xyz", SupportedFileType.OTHER),
        ("noextension", SupportedFileType.OTHER),
        ("UPPERCASE.PDF", SupportedFileType.PDF),
    ])
    def test_get_file_type(self, mock_telemetry_service, file_name, expected_type):
        """Test file type detection."""
        # Arrange
        command = BlobSampleCommand(telemetry_service=mock_telemetry_service)

        # Act
        result = command._get_file_type(file_name)

        # Assert
        assert result == expected_type

    def test_construct_blob_url(self, mock_telemetry_service):
        """Test blob URL construction."""
        # Arrange
        command = BlobSampleCommand(telemetry_service=mock_telemetry_service)

        # Act
        url1 = command._construct_blob_url("blob-name.pdf", "custom-container")
        url2 = command._construct_blob_url("blob-name.pdf", None)

        # Assert
        assert url1 == "https://storage.azure.com/custom-container/blob-name.pdf"
        assert url2 == "https://storage.azure.com/uploaded-files/blob-name.pdf"

    def test_blob_sample_command_result_to_dict(self):
        """Test BlobSampleCommandResult to_dict method."""
        # Arrange
        result = BlobSampleCommandResult(
            blob_url="https://storage.azure.com/files/test.pdf",
            file_size=1024,
            operation="upload"
        )

        # Act
        result_dict = result.to_dict()

        # Assert
        assert result_dict == {
            "blobUrl": "https://storage.azure.com/files/test.pdf",
            "fileSize": 1024,
            "operation": "upload"
        }

    @pytest.mark.asyncio
    async def test_execute_command_with_metadata(
        self, mock_telemetry_service, mock_blob_service, sample_context
    ):
        """Test command execution preserves metadata."""
        # Arrange
        command = BlobSampleCommand(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service
        )

        # Act
        await command.execute_command_async(sample_context)

        # Assert
        # Verify metadata was passed to blob service
        mock_blob_service.upload_blob_async.assert_called_once()
        call_args = mock_blob_service.upload_blob_async.call_args
        metadata = call_args[1]['metadata']
        assert metadata['chat_id'] == 'test-chat-123'
        assert metadata['agent_id'] == 'test-agent'
        assert metadata['file_type'] == 'pdf'
        assert metadata['original_name'] == 'test-document.pdf'