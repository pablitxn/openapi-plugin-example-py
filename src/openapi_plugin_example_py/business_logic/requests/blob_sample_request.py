"""Blob sample request models."""
from typing import Optional

from openapi_plugin_common import RequestBase
from pydantic import BaseModel, Field


class BlobSampleRequest(RequestBase):
    """Request model for blob sample endpoint."""
    
    file_name: str = Field(
        ...,
        description="Name of the file to upload",
        example="document.pdf",
        pattern=r"^[a-zA-Z0-9_\-\.]+$"
    )
    file_content_base64: str = Field(
        ...,
        description="Base64 encoded file content",
        min_length=1
    )
    container_name: Optional[str] = Field(
        default=None,
        description="Target container name (uses default if not specified)",
        pattern=r"^[a-z0-9\-]+$"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata to store with the blob"
    )


class BlobSampleResponse(BaseModel):
    """Response model for blob sample endpoint."""
    
    blob_url: str = Field(
        ...,
        description="URL of the uploaded blob"
    )
    file_size: int = Field(
        ...,
        description="Size of the uploaded file in bytes"
    )
    container: str = Field(
        ...,
        description="Container where the file was stored"
    )
    upload_time_ms: Optional[float] = Field(
        default=None,
        description="Upload time in milliseconds"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "blob_url": "https://storage.azure.com/uploaded-files/chat-123/20240115_120000_abc123_document.pdf",
                "file_size": 1024000,
                "container": "uploaded-files",
                "upload_time_ms": 234.56
            }
        }