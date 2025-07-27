"""GenEY API client implementation for the Example Plugin."""
from typing import Optional, List

from openapi_plugin_common import GenEYClientBase

from ...config import get_settings
from ..file_validation import FileTypeValidator


class GenEYClient(GenEYClientBase):
    """GenEY client implementation for Example Plugin.
    
    This class provides the specific configuration values needed
    for the Example Plugin to communicate with GenEY API.
    """
    
    def __init__(self, allowed_file_types: Optional[List[str]] = None):
        """Initialize GenEY client with plugin-specific settings.
        
        Args:
            allowed_file_types: List of allowed file types for this plugin
        """
        settings = get_settings()
        super().__init__(
            tenant_id=settings.security.tenant_id,
            client_secret=settings.security.client_secret
        )
        self._settings = settings
        
        # Initialize file validator with plugin's allowed types or from settings
        if allowed_file_types is None:
            allowed_file_types = settings.plugin_options.supported_file_types
        self.file_validator = FileTypeValidator(allowed_file_types)
    
    @property
    def client_id(self) -> str:
        """Plugin's client ID."""
        return self._settings.security.client_id
    
    @property
    def geney_client_id(self) -> str:
        """GenEY API client ID."""
        return self._settings.security.geney_client_id
    
    @property
    def geney_api_domain(self) -> str:
        """GenEY API domain URL."""
        return self._settings.security.geney_api_domain
    
    async def get_file_from_chat_validated(
        self,
        chat_id: str,
        file_name: str,
        user_token: str
    ) -> bytes:
        """Get file from chat with validation.
        
        This method validates the file type before retrieving it.
        
        Args:
            chat_id: Chat session ID
            file_name: Name of the file to retrieve
            user_token: User's JWT token
            
        Returns:
            File content as bytes
            
        Raises:
            ValueError: If file type is not allowed
            FileNotFoundError: If file is not found
            GenEYClientError: If request fails
        """
        # Validate file type
        self.file_validator.validate(file_name)
        
        # Get file using parent method
        return await self.get_file_from_chat(chat_id, file_name, user_token)