"""Unit tests for FilesystemBlobService."""
import json
import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from openapi_plugin_common import BlobItemInfo, SupportedFileType
from src.openapi_plugin_example_py.infrastructure.blob_storage.filesystem_service import (
    FilesystemBlobService
)


class TestFilesystemBlobService:
    """Test suite for FilesystemBlobService."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def blob_service(self, temp_dir):
        """Create a FilesystemBlobService instance."""
        return FilesystemBlobService(base_path=temp_dir)

    @pytest.mark.asyncio
    async def test_upload_blob_async_basic(self, blob_service, temp_dir):
        """Test basic blob upload."""
        # Arrange
        container_name = "test-container"
        blob_name = "test-file.txt"
        data = b"Hello, World!"

        # Act
        result = await blob_service.upload_blob_async(
            container_name=container_name,
            blob_name=blob_name,
            data=data
        )

        # Assert
        expected_path = Path(temp_dir) / container_name / blob_name
        assert result == f"file://{expected_path.absolute()}"
        assert expected_path.exists()
        assert expected_path.read_bytes() == data

    @pytest.mark.asyncio
    async def test_upload_blob_async_with_metadata(self, blob_service, temp_dir):
        """Test blob upload with metadata."""
        # Arrange
        container_name = "test-container"
        blob_name = "test-file.pdf"
        data = b"PDF content"
        metadata = {"author": "Test User", "version": "1.0"}
        content_type = "application/pdf"

        # Act
        result = await blob_service.upload_blob_async(
            container_name=container_name,
            blob_name=blob_name,
            data=data,
            content_type=content_type,
            metadata=metadata
        )

        # Assert
        blob_path = Path(temp_dir) / container_name / blob_name
        meta_path = blob_path.with_suffix(".pdf.meta")
        
        assert blob_path.exists()
        assert meta_path.exists()
        
        meta_data = json.loads(meta_path.read_text())
        assert meta_data["content_type"] == content_type
        assert meta_data["metadata"] == metadata
        assert meta_data["size"] == len(data)
        assert "created" in meta_data

    @pytest.mark.asyncio
    async def test_upload_blob_async_nested_path(self, blob_service, temp_dir):
        """Test blob upload with nested path."""
        # Arrange
        container_name = "test-container"
        blob_name = "folder1/folder2/test-file.txt"
        data = b"Nested file content"

        # Act
        result = await blob_service.upload_blob_async(
            container_name=container_name,
            blob_name=blob_name,
            data=data
        )

        # Assert
        expected_path = Path(temp_dir) / container_name / blob_name
        assert expected_path.exists()
        assert expected_path.read_bytes() == data

    @pytest.mark.asyncio
    async def test_download_blob_async_success(self, blob_service, temp_dir):
        """Test successful blob download."""
        # Arrange
        container_name = "test-container"
        blob_name = "test-file.txt"
        data = b"Download me!"
        
        # Upload first
        await blob_service.upload_blob_async(container_name, blob_name, data)

        # Act
        downloaded_data = await blob_service.download_blob_async(container_name, blob_name)

        # Assert
        assert downloaded_data == data

    @pytest.mark.asyncio
    async def test_download_blob_async_not_found(self, blob_service):
        """Test blob download when file doesn't exist."""
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Blob not found"):
            await blob_service.download_blob_async("container", "nonexistent.txt")

    @pytest.mark.asyncio
    async def test_delete_blob_async(self, blob_service, temp_dir):
        """Test blob deletion."""
        # Arrange
        container_name = "test-container"
        blob_name = "test-file.txt"
        data = b"Delete me!"
        
        # Upload blob with metadata
        await blob_service.upload_blob_async(
            container_name, blob_name, data,
            content_type="text/plain",
            metadata={"test": "value"}
        )
        
        blob_path = Path(temp_dir) / container_name / blob_name
        meta_path = blob_path.with_suffix(".txt.meta")
        
        assert blob_path.exists()
        assert meta_path.exists()

        # Act
        await blob_service.delete_blob_async(container_name, blob_name)

        # Assert
        assert not blob_path.exists()
        assert not meta_path.exists()

    @pytest.mark.asyncio
    async def test_blob_exists_async(self, blob_service):
        """Test blob existence check."""
        # Arrange
        container_name = "test-container"
        blob_name = "test-file.txt"
        data = b"I exist!"
        
        # Act & Assert - before upload
        assert not await blob_service.blob_exists_async(container_name, blob_name)
        
        # Upload blob
        await blob_service.upload_blob_async(container_name, blob_name, data)
        
        # Act & Assert - after upload
        assert await blob_service.blob_exists_async(container_name, blob_name)

    @pytest.mark.asyncio
    async def test_list_blobs_async_basic(self, blob_service):
        """Test basic blob listing."""
        # Arrange
        container_name = "test-container"
        blobs = [
            ("file1.txt", b"Content 1"),
            ("file2.pdf", b"Content 2"),
            ("folder/file3.jpg", b"Content 3")
        ]
        
        for blob_name, data in blobs:
            await blob_service.upload_blob_async(container_name, blob_name, data)

        # Act
        listed_blobs = []
        async for blob in blob_service.list_blobs_async(container_name):
            listed_blobs.append(blob)

        # Assert
        assert len(listed_blobs) == 3
        blob_names = [blob.name for blob in listed_blobs]
        assert "file1.txt" in blob_names
        assert "file2.pdf" in blob_names
        assert "folder/file3.jpg" in blob_names

    @pytest.mark.asyncio
    async def test_list_blobs_async_with_prefix(self, blob_service):
        """Test blob listing with prefix filter."""
        # Arrange
        container_name = "test-container"
        blobs = [
            ("prefix/file1.txt", b"Content 1"),
            ("prefix/file2.txt", b"Content 2"),
            ("other/file3.txt", b"Content 3")
        ]
        
        for blob_name, data in blobs:
            await blob_service.upload_blob_async(container_name, blob_name, data)

        # Act
        listed_blobs = []
        async for blob in blob_service.list_blobs_async(container_name, prefix="prefix/"):
            listed_blobs.append(blob)

        # Assert
        assert len(listed_blobs) == 2
        blob_names = [blob.name for blob in listed_blobs]
        assert "prefix/file1.txt" in blob_names
        assert "prefix/file2.txt" in blob_names
        assert "other/file3.txt" not in blob_names

    @pytest.mark.asyncio
    async def test_list_blobs_async_with_file_type(self, blob_service):
        """Test blob listing with file type filter."""
        # Arrange
        container_name = "test-container"
        blobs = [
            ("file1.txt", b"Text content"),
            ("file2.pdf", b"PDF content"),
            ("image.jpg", b"Image content"),
            ("data.json", b'{"key": "value"}')
        ]
        
        for blob_name, data in blobs:
            await blob_service.upload_blob_async(container_name, blob_name, data)

        # Act
        listed_blobs = []
        async for blob in blob_service.list_blobs_async(
            container_name, file_type=SupportedFileType.JPG
        ):
            listed_blobs.append(blob)

        # Assert
        assert len(listed_blobs) == 1
        assert listed_blobs[0].name == "image.jpg"

    @pytest.mark.asyncio
    async def test_get_blob_properties_async(self, blob_service):
        """Test getting blob properties."""
        # Arrange
        container_name = "test-container"
        blob_name = "test-file.txt"
        data = b"Test content"
        metadata = {"key": "value"}
        content_type = "text/plain"
        
        await blob_service.upload_blob_async(
            container_name, blob_name, data,
            content_type=content_type,
            metadata=metadata
        )

        # Act
        properties = await blob_service.get_blob_properties_async(container_name, blob_name)

        # Assert
        assert properties.name == blob_name
        assert properties.size == len(data)
        assert properties.content_type == content_type
        assert properties.metadata == metadata
        assert properties.created_on is not None

    @pytest.mark.asyncio
    async def test_get_blob_properties_async_not_found(self, blob_service):
        """Test getting properties of non-existent blob."""
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Blob not found"):
            await blob_service.get_blob_properties_async("container", "nonexistent.txt")

    @pytest.mark.asyncio
    async def test_create_container_if_not_exists_async(self, blob_service, temp_dir):
        """Test container creation."""
        # Arrange
        container_name = "new-container"
        container_path = Path(temp_dir) / container_name

        # Act
        await blob_service.create_container_if_not_exists_async(container_name)

        # Assert
        assert container_path.exists()
        assert container_path.is_dir()

    @pytest.mark.asyncio
    async def test_delete_container_async(self, blob_service, temp_dir):
        """Test container deletion."""
        # Arrange
        container_name = "delete-me"
        
        # Create container and add some blobs
        await blob_service.upload_blob_async(container_name, "file1.txt", b"Content 1")
        await blob_service.upload_blob_async(container_name, "file2.txt", b"Content 2")
        
        container_path = Path(temp_dir) / container_name
        assert container_path.exists()

        # Act
        await blob_service.delete_container_async(container_name)

        # Assert
        assert not container_path.exists()

    @pytest.mark.asyncio
    async def test_rename_file_async(self, blob_service):
        """Test file renaming."""
        # Arrange
        container_name = "test-container"
        old_name = "old-file.txt"
        new_name = "new-file.txt"
        data = b"Rename me!"
        metadata = {"original": "true"}
        
        await blob_service.upload_blob_async(
            container_name, old_name, data,
            content_type="text/plain",
            metadata=metadata
        )

        # Act
        await blob_service.rename_file_async(container_name, old_name, new_name)

        # Assert
        assert not await blob_service.blob_exists_async(container_name, old_name)
        assert await blob_service.blob_exists_async(container_name, new_name)
        
        # Verify content is preserved
        downloaded_data = await blob_service.download_blob_async(container_name, new_name)
        assert downloaded_data == data
        
        # Verify metadata is preserved
        properties = await blob_service.get_blob_properties_async(container_name, new_name)
        assert properties.metadata == metadata

    @pytest.mark.asyncio
    async def test_rename_file_async_not_found(self, blob_service):
        """Test renaming non-existent file."""
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="File not found"):
            await blob_service.rename_file_async("container", "nonexistent.txt", "new.txt")

    @pytest.mark.asyncio
    async def test_delete_folder_async(self, blob_service, temp_dir):
        """Test folder deletion."""
        # Arrange
        container_name = "test-container"
        folder_path = "test-folder"
        
        # Create files in folder
        await blob_service.upload_blob_async(
            container_name, f"{folder_path}/file1.txt", b"Content 1"
        )
        await blob_service.upload_blob_async(
            container_name, f"{folder_path}/subfolder/file2.txt", b"Content 2"
        )
        
        folder_full_path = Path(temp_dir) / container_name / folder_path
        assert folder_full_path.exists()

        # Act
        await blob_service.delete_folder_async(container_name, folder_path)

        # Assert
        assert not folder_full_path.exists()

    @pytest.mark.asyncio
    async def test_get_sas_urls(self, blob_service, temp_dir):
        """Test getting SAS URLs (file:// URLs for filesystem)."""
        # Arrange
        container_name = "test-container"
        blob_names = ["file1.txt", "file2.txt", "nonexistent.txt"]
        
        # Upload some blobs
        await blob_service.upload_blob_async(container_name, blob_names[0], b"Content 1")
        await blob_service.upload_blob_async(container_name, blob_names[1], b"Content 2")

        # Act
        urls = await blob_service.get_sas_urls(container_name, blob_names)

        # Assert
        assert len(urls) == 2  # Only existing files
        assert blob_names[0] in urls
        assert blob_names[1] in urls
        assert blob_names[2] not in urls
        
        # Verify URLs are correct
        expected_path1 = Path(temp_dir) / container_name / blob_names[0]
        assert urls[blob_names[0]] == f"file://{expected_path1.absolute()}"

    @pytest.mark.asyncio
    async def test_get_all_blobs(self, blob_service):
        """Test getting all blobs in a container."""
        # Arrange
        container_name = "test-container"
        expected_blobs = [
            ("file1.txt", b"Content 1"),
            ("file2.pdf", b"Content 2"),
            ("folder/file3.jpg", b"Content 3")
        ]
        
        for blob_name, data in expected_blobs:
            await blob_service.upload_blob_async(container_name, blob_name, data)

        # Act
        all_blobs = await blob_service.get_all_blobs(container_name)

        # Assert
        assert len(all_blobs) == 3
        blob_names = [blob.name for blob in all_blobs]
        for expected_name, _ in expected_blobs:
            assert expected_name in blob_names

    def test_initialization_creates_base_path(self, temp_dir):
        """Test that initialization creates the base path directory."""
        # Arrange
        base_path = Path(temp_dir) / "new_storage"
        assert not base_path.exists()

        # Act
        service = FilesystemBlobService(base_path=str(base_path))

        # Assert
        assert base_path.exists()
        assert base_path.is_dir()