"""File validation configuration for the Example Plugin."""
from openapi_plugin_common import FileTypeValidator

# Default allowed types for this plugin
DEFAULT_ALLOWED_TYPES = ["pdf", "txt", "docx", "json", "csv", "xlsx"]


def create_geney_validator(allowed_types=None):
    """Create a file validator for this plugin with GenEY support.
    
    Args:
        allowed_types: List of allowed file extensions. If None, uses default.
        
    Returns:
        FileTypeValidator configured for GenEY
    """
    return FileTypeValidator.create_for_geney(
        allowed_types=allowed_types or DEFAULT_ALLOWED_TYPES
    )