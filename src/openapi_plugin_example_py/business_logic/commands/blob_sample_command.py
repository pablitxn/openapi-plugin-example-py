"""Blob sample command implementation."""
import json
from typing import Optional

from openapi_plugin_common import (
    CommandBase,
    CommandContextBase,
    CommandException,
    ConfigurationException,
    SupportedFileType,
    ValidationException,
)

from ..options import ExamplePluginOptions


class BlobSampleCommandContext(CommandContextBase):
    """Context for the blob sample command."""
    
    file_name: str
    file_content: bytes
    container_name: Optional[str] = None
    metadata: dict = {}


class BlobSampleCommandResult:
    """Result from the blob sample command."""
    
    def __init__(
        self,
        blob_url: str,
        file_size: int,
        operation: str = "upload"
    ):
        self.blob_url = blob_url
        self.file_size = file_size
        self.operation = operation
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "blobUrl": self.blob_url,
            "fileSize": self.file_size,
            "operation": self.operation
        }


class BlobSampleCommand(CommandBase[BlobSampleCommandContext, ExamplePluginOptions]):
    """Command to handle blob storage operations."""
    
    def __init__(
        self,
        telemetry_service: Optional[object] = None,
        blob_service: Optional[object] = None
    ) -> None:
        """Initialize the command."""
        super().__init__(telemetry_service)
        self._blob_service = blob_service
    
    async def execute_command_async(self, context: BlobSampleCommandContext) -> None:
        """Execute the blob sample command logic."""
        # Validate blob service
        if not self._blob_service:
            raise ConfigurationException("Blob service is not configured")
        
        # Validate file size
        max_size_bytes = getattr(self, "_options", {}).get("max_file_size_mb", 10) * 1024 * 1024
        if len(context.file_content) > max_size_bytes:
            raise ValidationException(f"File size exceeds maximum allowed size of {max_size_bytes} bytes")
        
        # Determine file type
        file_type = self._get_file_type(context.file_name)
        
        # Upload the blob
        result = await self._upload_blob(context, file_type)
        
        # Store result in context metadata
        context.metadata["result"] = result
        
        # Log telemetry
        if self._telemetry_service and hasattr(self._telemetry_service, "log_event"):
            self._telemetry_service.log_event("BlobUploaded", {
                "ChatId": context.chat_id,
                "FileName": context.file_name,
                "FileSize": str(len(context.file_content)),
                "FileType": file_type.value,
                "Container": context.container_name or "default"
            })
    
    async def _upload_blob(
        self,
        context: BlobSampleCommandContext,
        file_type: SupportedFileType
    ) -> BlobSampleCommandResult:
        """Upload blob to storage."""
        try:
            # Prepare metadata
            metadata = {
                "chat_id": context.chat_id,
                "agent_id": context.agent_id,
                "file_type": file_type.value,
                "original_name": context.file_name
            }
            
            # Create unique blob name
            import uuid
            from datetime import datetime
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            blob_name = f"{context.chat_id}/{timestamp}_{unique_id}_{context.file_name}"
            
            # Upload to blob storage
            blob_url = await self._blob_service.upload_blob_async(
                container_name=context.container_name or "dev-uploads",
                blob_name=blob_name,
                data=context.file_content,
                content_type=f"application/{file_type.value}",
                metadata=metadata
            )
            
            return BlobSampleCommandResult(
                blob_url=blob_url,
                file_size=len(context.file_content),
                operation="upload"
            )
            
        except Exception as e:
            if self._telemetry_service and hasattr(self._telemetry_service, "log_error"):
                self._telemetry_service.log_error(
                    f"Blob upload failed: {str(e)}",
                    {
                        "Error": str(e),
                        "ChatId": context.chat_id,
                        "FileName": context.file_name
                    }
                )
            raise CommandException(f"Failed to upload blob: {str(e)}") from e
    
    def _get_file_type(self, file_name: str) -> SupportedFileType:
        """Determine file type from filename."""
        extension = file_name.lower().split('.')[-1] if '.' in file_name else ''
        
        type_mapping = {
            'pdf': SupportedFileType.PDF,
            'png': SupportedFileType.IMAGE,
            'jpg': SupportedFileType.IMAGE,
            'jpeg': SupportedFileType.IMAGE,
            'txt': SupportedFileType.TEXT,
            'json': SupportedFileType.JSON,
            'csv': SupportedFileType.CSV,
            'xlsx': SupportedFileType.EXCEL,
            'xls': SupportedFileType.EXCEL,
            'docx': SupportedFileType.WORD,
            'doc': SupportedFileType.WORD,
            'pptx': SupportedFileType.POWERPOINT,
            'ppt': SupportedFileType.POWERPOINT,
            'zip': SupportedFileType.ZIP
        }
        
        return type_mapping.get(extension, SupportedFileType.OTHER)
    
    def _construct_blob_url(self, blob_name: str, container_name: Optional[str]) -> str:
        """Construct blob URL."""
        # In a real implementation, this would get the actual URL from blob service
        # For now, return a placeholder
        container = container_name or "uploaded-files"
        return f"https://storage.azure.com/{container}/{blob_name}"