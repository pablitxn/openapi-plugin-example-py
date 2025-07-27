"""Unit tests for BlobSampleHandler."""
import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from openapi_plugin_common import ValidationException
from src.openapi_plugin_example_py.business_logic.handlers.blob_sample_handler import (
    BlobSampleHandler
)
from src.openapi_plugin_example_py.business_logic.commands.blob_sample_command import (
    BlobSampleCommand,
    BlobSampleCommandContext,
    BlobSampleCommandResult
)
from src.openapi_plugin_example_py.business_logic.requests.blob_sample_request import (
    BlobSampleRequest,
    BlobSampleResponse
)
from src.openapi_plugin_example_py.business_logic.options.plugin_options import (
    ExamplePluginOptions
)


class TestBlobSampleHandler:
    """Test suite for BlobSampleHandler."""

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
        options = ExamplePluginOptions()
        options.max_file_size_mb = 10
        options.supported_file_types = ['pdf', 'txt', 'jpg', 'png', 'xlsx', 'docx']
        return options

    @pytest.fixture
    def mock_telemetry_service(self):
        """Create a mock telemetry service."""
        service = MagicMock()
        return service

    @pytest.fixture
    def sample_request(self):
        """Create a sample request."""
        file_content = b"This is test file content"
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        return BlobSampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            file_name="test-document.pdf",
            file_content_base64=encoded_content,
            container_name=None,
            metadata={"key": "value"}
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
        handler = BlobSampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock the execute_command_async to populate context metadata
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = BlobSampleCommandResult(
                blob_url="https://storage.azure.com/uploaded-files/test-document.pdf",
                file_size=25,  # Size of "This is test file content"
                operation="upload"
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        with patch('time.time', side_effect=[0, 0.15]):  # 150ms upload time
            response = await handler.execute_async(sample_request)

        # Assert
        assert isinstance(response, BlobSampleResponse)
        assert response.blob_url == "https://storage.azure.com/uploaded-files/test-document.pdf"
        assert response.file_size == 25
        assert response.container == "uploaded-files"
        assert response.upload_time_ms == 150.0

        # Verify command execution
        handler.execute_command_async.assert_called_once()
        call_args = handler.execute_command_async.call_args
        assert call_args[0][0] == BlobSampleCommand
        context = call_args[0][1]
        assert isinstance(context, BlobSampleCommandContext)
        assert context.file_name == "test-document.pdf"
        assert context.file_content == b"This is test file content"
        assert context.metadata.get("key") == "value"

    @pytest.mark.asyncio
    async def test_execute_async_invalid_base64(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution with invalid base64 content."""
        # Arrange
        request = BlobSampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            file_name="test.pdf",
            file_content_base64="invalid-base64-content!@#",
            container_name=None
        )
        
        handler = BlobSampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )

        # Act & Assert
        with pytest.raises(ValidationException, match="Invalid base64 content"):
            await handler.execute_async(request)

    @pytest.mark.asyncio
    async def test_execute_async_file_too_large(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution with file too large."""
        # Arrange
        plugin_options.max_file_size_mb = 0.00001  # Very small limit
        large_content = b"x" * 1000
        encoded_content = base64.b64encode(large_content).decode('utf-8')
        
        request = BlobSampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            file_name="large-file.pdf",
            file_content_base64=encoded_content,
            container_name=None
        )
        
        handler = BlobSampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )

        # Act & Assert
        with pytest.raises(ValidationException, match="File size .* exceeds maximum"):
            await handler.execute_async(request)

    @pytest.mark.asyncio
    async def test_execute_async_unsupported_file_type(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution with unsupported file type."""
        # Arrange
        content = b"test content"
        encoded_content = base64.b64encode(content).decode('utf-8')
        
        request = BlobSampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            file_name="test-file.exe",  # Unsupported type
            file_content_base64=encoded_content,
            container_name=None
        )
        
        handler = BlobSampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )

        # Act & Assert
        with pytest.raises(ValidationException, match="File type 'exe' is not supported"):
            await handler.execute_async(request)

    @pytest.mark.asyncio
    async def test_execute_async_with_custom_container(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution with custom container name."""
        # Arrange
        content = b"test content"
        encoded_content = base64.b64encode(content).decode('utf-8')
        
        request = BlobSampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            file_name="test.txt",
            file_content_base64=encoded_content,
            container_name="custom-container",
            metadata=None
        )
        
        handler = BlobSampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        # Mock result
        async def mock_execute_command(command_class, context):
            context.metadata["result"] = BlobSampleCommandResult(
                blob_url="https://storage.azure.com/custom-container/test.txt",
                file_size=12,
                operation="upload"
            )
        
        handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)

        # Act
        response = await handler.execute_async(request)

        # Assert
        assert response.container == "custom-container"
        
        # Verify context was created with custom container
        call_args = handler.execute_command_async.call_args
        context = call_args[0][1]
        assert context.container_name == "custom-container"

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
        handler = BlobSampleHandler(
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
    async def test_execute_async_file_without_extension(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution with file without extension."""
        # Arrange
        content = b"test content"
        encoded_content = base64.b64encode(content).decode('utf-8')
        
        request = BlobSampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            file_name="no_extension",  # No file extension
            file_content_base64=encoded_content,
            container_name=None
        )
        
        handler = BlobSampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )

        # Act & Assert
        with pytest.raises(ValidationException, match="File type '' is not supported"):
            await handler.execute_async(request)

    @pytest.mark.parametrize("file_name,expected_valid", [
        ("document.pdf", True),
        ("file.txt", True),
        ("image.jpg", True),
        ("photo.png", True),
        ("spreadsheet.xlsx", True),
        ("report.docx", True),
        ("UPPERCASE.PDF", True),
        ("script.sh", False),
        ("archive.zip", False),
    ])
    @pytest.mark.asyncio
    async def test_execute_async_file_type_validation(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service,
        file_name,
        expected_valid
    ):
        """Test file type validation."""
        # Arrange
        content = b"test content"
        encoded_content = base64.b64encode(content).decode('utf-8')
        
        request = BlobSampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            file_name=file_name,
            file_content_base64=encoded_content,
            container_name=None
        )
        
        handler = BlobSampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        if expected_valid:
            # Mock successful execution
            async def mock_execute_command(command_class, context):
                context.metadata["result"] = BlobSampleCommandResult(
                    blob_url=f"https://storage.azure.com/files/{file_name}",
                    file_size=12,
                    operation="upload"
                )
            
            handler.execute_command_async = AsyncMock(side_effect=mock_execute_command)
            
            # Act
            response = await handler.execute_async(request)
            
            # Assert
            assert response.blob_url == f"https://storage.azure.com/files/{file_name}"
        else:
            # Act & Assert
            with pytest.raises(ValidationException, match="is not supported"):
                await handler.execute_async(request)

    @pytest.mark.asyncio
    async def test_execute_async_context_metadata_merge(
        self,
        mock_command_invoker_factory,
        plugin_options,
        mock_telemetry_service
    ):
        """Test that request metadata is properly merged into context."""
        # Arrange
        content = b"test"
        encoded_content = base64.b64encode(content).decode('utf-8')
        
        request = BlobSampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            file_name="test.pdf",
            file_content_base64=encoded_content,
            container_name=None,
            metadata={"key1": "value1", "key2": "value2"}
        )
        
        handler = BlobSampleHandler(
            command_invoker_factory=mock_command_invoker_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )
        
        captured_context = None
        
        async def capture_context(command_class, context):
            nonlocal captured_context
            captured_context = context
            context.metadata["result"] = BlobSampleCommandResult(
                blob_url="https://test.com/file.pdf",
                file_size=4,
                operation="upload"
            )
        
        handler.execute_command_async = AsyncMock(side_effect=capture_context)

        # Act
        await handler.execute_async(request)

        # Assert
        assert captured_context is not None
        assert captured_context.metadata.get("key1") == "value1"
        assert captured_context.metadata.get("key2") == "value2"