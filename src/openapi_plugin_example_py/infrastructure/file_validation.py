"""File validation utilities for GenEY integration."""
from typing import List, Optional, Set


class FileTypeValidator:
    """Validates file types supported by GenEY."""
    
    # File types that GenEY supports natively
    GENEY_SUPPORTED_TYPES: Set[str] = {
        # Documents
        "pdf", "txt", "docx", "doc", "rtf",
        # Data files
        "json", "csv", "xlsx", "xls",
        # Images (for multimodal processing)
        "png", "jpg", "jpeg", "gif", "bmp",
        # Code files
        "py", "js", "ts", "java", "cs", "cpp", "c", "h",
        "xml", "yaml", "yml", "html", "css",
        # Archives (may need special handling)
        "zip", "tar", "gz"
    }
    
    # Plugin-specific allowed types (subset of GenEY supported types)
    DEFAULT_ALLOWED_TYPES: Set[str] = {
        "pdf", "txt", "docx", "json", "csv", "xlsx"
    }
    
    def __init__(self, allowed_types: Optional[List[str]] = None):
        """Initialize file type validator.
        
        Args:
            allowed_types: List of allowed file extensions. If None, uses default.
        """
        if allowed_types:
            # Validate that all allowed types are supported by GenEY
            self.allowed_types = set()
            for file_type in allowed_types:
                if file_type.lower() in self.GENEY_SUPPORTED_TYPES:
                    self.allowed_types.add(file_type.lower())
                else:
                    raise ValueError(
                        f"File type '{file_type}' is not supported by GenEY. "
                        f"Supported types: {', '.join(sorted(self.GENEY_SUPPORTED_TYPES))}"
                    )
        else:
            self.allowed_types = self.DEFAULT_ALLOWED_TYPES.copy()
    
    def is_valid(self, filename: str) -> bool:
        """Check if a file type is valid.
        
        Args:
            filename: Name of the file to validate
            
        Returns:
            True if file type is allowed, False otherwise
        """
        if not filename or '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in self.allowed_types
    
    def validate(self, filename: str) -> None:
        """Validate a file type, raising exception if invalid.
        
        Args:
            filename: Name of the file to validate
            
        Raises:
            ValueError: If file type is not allowed
        """
        if not self.is_valid(filename):
            extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
            raise ValueError(
                f"File type '{extension}' is not allowed. "
                f"Allowed types: {', '.join(sorted(self.allowed_types))}"
            )
    
    @classmethod
    def is_geney_supported(cls, filename: str) -> bool:
        """Check if a file type is supported by GenEY.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if file type is supported by GenEY, False otherwise
        """
        if not filename or '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in cls.GENEY_SUPPORTED_TYPES
    
    def get_allowed_types(self) -> List[str]:
        """Get list of allowed file types.
        
        Returns:
            Sorted list of allowed file extensions
        """
        return sorted(self.allowed_types)
    
    @classmethod
    def get_geney_supported_types(cls) -> List[str]:
        """Get list of all GenEY supported file types.
        
        Returns:
            Sorted list of GenEY supported file extensions
        """
        return sorted(cls.GENEY_SUPPORTED_TYPES)