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
        
        # Create a mock command that will raise ValidationException
        mock_command = AsyncMock()
        mock_command.handle_async.side_effect = ValidationException("Invalid base64 content")
        
        # Configure factory to return our mock command
        factory.create.return_value = mock_command
        
        return factory

    @pytest.fixture
    def plugin_options(self):
        """Create plugin options."""
        from openapi_plugin_common import SchemasConfig
        options = ExamplePluginOptions(
            schemas=SchemasConfig(
                sample='{}',
                ai_sample='{}'
            )
        )
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
    async def test_handle_async_success(
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
            response = await handler.handle_async(sample_request)

        # Assert
        assert isinstance(response, BlobSampleResponse)
        assert response.blob_url == "https://storage.azure.com/uploaded-files/test-document.pdf"
        assert response.file_size == 25
        assert response.container == "uploaded-files"
        assert response.upload_time_ms == 0  # Handler sets it to 0, controller would set actual value

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
    async def test_handle_async_invalid_base64(
        self,
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
            file_content_base64="this is definitely not base64!",
            container_name=None
        )
        
        # Create a mock blob service
        mock_blob_service = AsyncMock()
        
        # Create a custom command factory with blob service
        from src.openapi_plugin_example_py.infrastructure import CustomCommandInvokerFactory
        command_factory = CustomCommandInvokerFactory(
            telemetry_service=mock_telemetry_service,
            blob_service=mock_blob_service,
            enable_command_logging=False
        )
        
        handler = BlobSampleHandler(
            command_invoker_factory=command_factory,
            plugin_options=plugin_options,
            telemetry_service=mock_telemetry_service
        )

        # Act & Assert
        with pytest.raises(ValidationException, match="Invalid base64 content"):
            await handler.handle_async(request)

    @pytest.mark.asyncio
    async def test_handle_async_file_too_large(
        self,
        plugin_options,
        mock_telemetry_service
    ):
        """Test handler execution with file too large."""
        # Arrange
        # Create custom options with small file size limit
        from openapi_plugin_common import SchemasConfig
        custom_options = ExamplePluginOptions(
            schemas=SchemasConfig(
                sample='{}',
                ai_sample='{}'
            ),
            max_file_size_mb=1,  # 1 MB limit
            supported_file_types=plugin_options.supported_file_types
        )
        large_content = b"x" * (2 * 1024 * 1024)  # 2 MB
        encoded_content = base64.b64encode(large_content).decode('utf-8')
        
        request = BlobSampleRequest(
            chat_id="test-chat-123",
            agent_id="test-agent",
            agent_version="1.0.0",
            file_name="large-file.pdf",
            file_content_base64=encoded_content,
            container_name=None
        )
        
        # Create a custom command factory that won't interfere
        from src.openapi_plugin_example_py.infrastructure import CustomCommandInvokerFactory
        command_factory = CustomCommandInvokerFactory(
            telemetry_service=mock_telemetry_service,
            enable_command_logging=False
        )
        
        handler = BlobSampleHandler(
            command_invoker_factory=command_factory,
            plugin_options=custom_options,
            telemetry_service=mock_telemetry_service
        )

        # Act & Assert
        with pytest.raises(ValidationException, match="exceeds maximum allowed size"):
            await handler.handle_async(request)

    @pytest.mark.asyncio
    async def test_handle_async_unsupported_file_type(
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
            await handler.handle_async(request)

    @pytest.mark.asyncio
    async def test_handle_async_with_custom_container(
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
        response = await handler.handle_async(request)

        # Assert
        assert response.container == "custom-container"
        
        # Verify context was created with custom container
        call_args = handler.execute_command_async.call_args
        context = call_args[0][1]
        assert context.container_name == "custom-container"

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
            await handler.handle_async(sample_request)

    @pytest.mark.asyncio
    async def test_handle_async_file_without_extension(
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
            await handler.handle_async(request)

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
    async def test_handle_async_file_type_validation(
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
            response = await handler.handle_async(request)
            
            # Assert
            assert response.blob_url == f"https://storage.azure.com/files/{file_name}"
        else:
            # Act & Assert
            with pytest.raises(ValidationException, match="is not supported"):
                await handler.handle_async(request)

    @pytest.mark.asyncio
    async def test_handle_async_context_metadata_merge(
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
        await handler.handle_async(request)

        # Assert
        assert captured_context is not None
        assert captured_context.metadata.get("key1") == "value1"
        assert captured_context.metadata.get("key2") == "value2"