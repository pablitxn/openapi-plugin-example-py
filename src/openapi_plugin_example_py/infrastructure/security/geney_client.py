"""GenEY API client for accessing files uploaded in chat."""
import os
from typing import Optional

import httpx
import msal


class GenEYClient:
    """Client for accessing GenEY API using On-Behalf-Of flow."""
    
    def __init__(
        self,
        client_id: str,
        tenant_id: str = "5b973f99-77df-4beb-b27d-aa0c70b8482c",
        geney_client_id: str = None,
        geney_api_domain: str = None
    ):
        """Initialize GenEY client."""
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.geney_client_id = geney_client_id
        self.geney_api_domain = geney_api_domain
        
        # Get client secret from environment
        self.client_secret = os.environ.get("clientSecret")
        if not self.client_secret:
            raise ValueError("clientSecret environment variable not set")
        
        # Create MSAL application
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.app = msal.ConfidentialClientApplication(
            client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        # API scope for GenEY
        self.api_scope = [f"api://{geney_client_id}/user_impersonation"]
    
    async def get_access_token(self, user_token: str) -> str:
        """Get access token for GenEY API using On-Behalf-Of flow."""
        # Extract the actual token if it includes "Bearer "
        if user_token.startswith("Bearer "):
            user_token = user_token.split(" ")[1]
        
        # Acquire token on behalf of user
        result = self.app.acquire_token_on_behalf_of(
            user_assertion=user_token,
            scopes=self.api_scope
        )
        
        if "access_token" in result:
            return result["access_token"]
        else:
            error = result.get("error", "Unknown error")
            error_description = result.get("error_description", "No description")
            raise Exception(f"Failed to acquire token: {error} - {error_description}")
    
    async def get_file_from_chat(
        self,
        chat_id: str,
        file_name: str,
        user_token: str
    ) -> bytes:
        """Get file content from GenEY chat storage."""
        # Get access token for GenEY
        access_token = await self.get_access_token(user_token)
        
        # Construct URL
        url = f"{self.geney_api_domain}/documents/chats/{chat_id}/file/{file_name}"
        
        # Make request to GenEY API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/octet-stream"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.content
            elif response.status_code == 404:
                raise FileNotFoundError(f"File '{file_name}' not found in chat '{chat_id}'")
            else:
                raise Exception(
                    f"Failed to get file from GenEY: {response.status_code} - {response.text}"
                )
    
    async def list_chat_files(
        self,
        chat_id: str,
        user_token: str
    ) -> list:
        """List files in a chat."""
        # Get access token for GenEY
        access_token = await self.get_access_token(user_token)
        
        # Construct URL
        url = f"{self.geney_api_domain}/documents/chats/{chat_id}/files"
        
        # Make request to GenEY API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(
                    f"Failed to list files from GenEY: {response.status_code} - {response.text}"
                )