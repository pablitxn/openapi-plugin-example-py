"""Blob sample request handler."""
import base64
import time
from typing import Optional

from openapi_plugin_common import CommandInvoker, RequestHandlerBase

from ..commands import BlobSampleCommand, BlobSampleCommandContext
from ..options import ExamplePluginOptions
from ..requests import BlobSampleRequest, BlobSampleResponse


class BlobSampleHandler(RequestHandlerBase[BlobSampleRequest, BlobSampleResponse]):
    """Handler for blob sample requests."""
    
    def __init__(
        self,
        command_invoker_factory,
        plugin_options: ExamplePluginOptions,
        telemetry_service: Optional[object] = None
    ) -> None:
        """Initialize the handler."""
        super().__init__(telemetry_service)
        self._command_invoker_factory = command_invoker_factory
        self._plugin_options = plugin_options
    
    async def execute_async(self, request: BlobSampleRequest) -> BlobSampleResponse:
        """Execute the blob sample request."""
        start_time = time.time()
        
        # Decode base64 content
        try:
            file_content = base64.b64decode(request.file_content_base64)
        except Exception as e:
            raise ValueError(f"Invalid base64 content: {str(e)}")
        
        # Validate file size
        max_size_bytes = self._plugin_options.max_file_size_mb * 1024 * 1024
        if len(file_content) > max_size_bytes:
            raise ValueError(
                f"File size ({len(file_content)} bytes) exceeds maximum "
                f"allowed size ({max_size_bytes} bytes)"
            )
        
        # Validate file type
        file_extension = request.file_name.split('.')[-1].lower() if '.' in request.file_name else ''
        if file_extension not in self._plugin_options.supported_file_types:
            raise ValueError(
                f"File type '{file_extension}' is not supported. "
                f"Supported types: {', '.join(self._plugin_options.supported_file_types)}"
            )
        
        # Create command context
        context = BlobSampleCommandContext(
            chat_id=request.chat_id,
            agent_id=request.agent_id,
            agent_version=request.agent_version,
            file_name=request.file_name,
            file_content=file_content,
            container_name=request.container_name
        )
        
        # Add metadata if provided
        if request.metadata:
            context.metadata.update(request.metadata)
        
        # Create and execute command
        command_invoker = self._command_invoker_factory.create(BlobSampleCommand)
        await command_invoker.invoke_async(context, self._plugin_options)
        
        # Get result from context metadata
        result = context.metadata.get("result")
        if not result:
            raise ValueError("Command did not produce a result")
        
        # Calculate upload time
        upload_time_ms = (time.time() - start_time) * 1000
        
        # Create response
        return BlobSampleResponse(
            blob_url=result.blob_url,
            file_size=result.file_size,
            container=request.container_name or "uploaded-files",
            upload_time_ms=upload_time_ms
        )