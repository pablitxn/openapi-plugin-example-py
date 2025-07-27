"""Filesystem-based blob storage service for development/testing."""
import os
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional, List, Dict
from openapi_plugin_common import IBlobService, BlobItemInfo, SupportedFileType


class FilesystemBlobService(IBlobService):
    """Filesystem implementation of blob storage for development."""
    
    def __init__(self, base_path: str = "./mock_storage"):
        """Initialize filesystem blob service.
        
        Args:
            base_path: Base directory for storing files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_container_path(self, container_name: str) -> Path:
        """Get the path for a container."""
        container_path = self.base_path / container_name
        container_path.mkdir(parents=True, exist_ok=True)
        return container_path
    
    def _get_blob_path(self, container_name: str, blob_name: str) -> Path:
        """Get the full path for a blob."""
        return self._get_container_path(container_name) / blob_name
    
    async def upload_blob_async(
        self,
        container_name: str,
        blob_name: str,
        data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """Upload a blob to filesystem."""
        blob_path = self._get_blob_path(container_name, blob_name)
        blob_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the actual data
        blob_path.write_bytes(data)
        
        # Store metadata in a separate file
        if metadata or content_type:
            meta_path = blob_path.with_suffix(blob_path.suffix + ".meta")
            meta_data = {
                "content_type": content_type,
                "metadata": metadata or {},
                "created": datetime.now(timezone.utc).isoformat(),
                "size": len(data)
            }
            meta_path.write_text(json.dumps(meta_data, indent=2))
        
        return f"file://{blob_path.absolute()}"
    
    async def download_blob_async(self, container_name: str, blob_name: str) -> bytes:
        """Download a blob from filesystem."""
        blob_path = self._get_blob_path(container_name, blob_name)
        
        if not blob_path.exists():
            raise FileNotFoundError(f"Blob not found: {container_name}/{blob_name}")
        
        return blob_path.read_bytes()
    
    async def delete_blob_async(self, container_name: str, blob_name: str) -> None:
        """Delete a blob from filesystem."""
        blob_path = self._get_blob_path(container_name, blob_name)
        meta_path = blob_path.with_suffix(blob_path.suffix + ".meta")
        
        if blob_path.exists():
            blob_path.unlink()
        
        if meta_path.exists():
            meta_path.unlink()
    
    async def list_blobs_async(
        self,
        container_name: str,
        prefix: Optional[str] = None,
        file_type: Optional[SupportedFileType] = None
    ) -> AsyncGenerator[BlobItemInfo, None]:
        """List blobs in a container."""
        container_path = self._get_container_path(container_name)
        
        for file_path in container_path.rglob("*"):
            if file_path.is_file() and not file_path.suffix == ".meta":
                relative_path = file_path.relative_to(container_path)
                blob_name = str(relative_path)
                
                # Apply prefix filter
                if prefix and not blob_name.startswith(prefix):
                    continue
                
                # Apply file type filter
                if file_type:
                    allowed_extensions = {
                        SupportedFileType.CSV: [".csv"],
                        SupportedFileType.EXCEL: [".xlsx", ".xls"],
                        SupportedFileType.JSON: [".json"],
                        SupportedFileType.TEXT: [".txt"],
                        SupportedFileType.IMAGE: [".png", ".jpg", ".jpeg", ".gif", ".bmp"],
                        SupportedFileType.PDF: [".pdf"]
                    }.get(file_type, [])
                    
                    if not any(blob_name.lower().endswith(ext) for ext in allowed_extensions):
                        continue
                
                # Load metadata if exists
                meta_path = file_path.with_suffix(file_path.suffix + ".meta")
                metadata = {}
                content_type = None
                
                if meta_path.exists():
                    try:
                        meta_data = json.loads(meta_path.read_text())
                        metadata = meta_data.get("metadata", {})
                        content_type = meta_data.get("content_type")
                    except:
                        pass
                
                yield BlobItemInfo(
                    name=blob_name,
                    size=file_path.stat().st_size,
                    created_on=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    content_type=content_type,
                    metadata=metadata
                )
    
    async def blob_exists_async(self, container_name: str, blob_name: str) -> bool:
        """Check if a blob exists."""
        blob_path = self._get_blob_path(container_name, blob_name)
        return blob_path.exists()
    
    async def get_blob_properties_async(
        self, container_name: str, blob_name: str
    ) -> BlobItemInfo:
        """Get blob properties."""
        blob_path = self._get_blob_path(container_name, blob_name)
        
        if not blob_path.exists():
            raise FileNotFoundError(f"Blob not found: {container_name}/{blob_name}")
        
        # Load metadata if exists
        meta_path = blob_path.with_suffix(blob_path.suffix + ".meta")
        metadata = {}
        content_type = None
        
        if meta_path.exists():
            try:
                meta_data = json.loads(meta_path.read_text())
                metadata = meta_data.get("metadata", {})
                content_type = meta_data.get("content_type")
            except:
                pass
        
        return BlobItemInfo(
            name=blob_name,
            size=blob_path.stat().st_size,
            created_on=datetime.fromtimestamp(blob_path.stat().st_mtime).isoformat(),
            content_type=content_type,
            metadata=metadata
        )
    
    async def create_container_if_not_exists_async(self, container_name: str) -> None:
        """Create a container if it doesn't exist."""
        self._get_container_path(container_name)  # This creates the directory
    
    async def delete_container_async(self, container_name: str) -> None:
        """Delete a container and all its contents."""
        container_path = self._get_container_path(container_name)
        if container_path.exists():
            shutil.rmtree(container_path)
    
    # Additional methods required by IBlobService interface
    async def delete_file_async(self, container_name: str, file_path: str) -> None:
        """Delete a file from storage."""
        await self.delete_blob_async(container_name, file_path)
    
    async def delete_folder_async(self, container_name: str, folder_path: str) -> None:
        """Delete a folder and all its contents."""
        folder_full_path = self._get_blob_path(container_name, folder_path)
        if folder_full_path.exists() and folder_full_path.is_dir():
            shutil.rmtree(folder_full_path)
    
    async def get_all_blobs(self, container_name: str) -> List[BlobItemInfo]:
        """Get all blobs in a container."""
        blobs = []
        async for blob in self.list_blobs_async(container_name):
            blobs.append(blob)
        return blobs
    
    async def get_file_by_id_async(self, container_name: str, file_id: str) -> bytes:
        """Get file by ID (same as blob name for filesystem)."""
        return await self.download_blob_async(container_name, file_id)
    
    async def get_file_from_storage_async(self, container_name: str, file_path: str) -> bytes:
        """Get file from storage."""
        return await self.download_blob_async(container_name, file_path)
    
    async def get_sas_urls(self, container_name: str, blob_names: List[str]) -> Dict[str, str]:
        """Get SAS URLs for blobs (returns file:// URLs for filesystem)."""
        urls = {}
        for blob_name in blob_names:
            blob_path = self._get_blob_path(container_name, blob_name)
            if blob_path.exists():
                urls[blob_name] = f"file://{blob_path.absolute()}"
        return urls
    
    async def rename_file_async(self, container_name: str, old_name: str, new_name: str) -> None:
        """Rename a file in storage."""
        old_path = self._get_blob_path(container_name, old_name)
        new_path = self._get_blob_path(container_name, new_name)
        
        if not old_path.exists():
            raise FileNotFoundError(f"File not found: {container_name}/{old_name}")
        
        # Ensure parent directory exists
        new_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        old_path.rename(new_path)
        
        # Move metadata if exists
        old_meta = old_path.with_suffix(old_path.suffix + ".meta")
        if old_meta.exists():
            new_meta = new_path.with_suffix(new_path.suffix + ".meta")
            old_meta.rename(new_meta)