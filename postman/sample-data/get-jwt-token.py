#!/usr/bin/env python3
"""
Helper script to obtain JWT token for testing the OpenAPI Plugin.
Requires: pip install msal
"""

import os
import sys
from msal import ConfidentialClientApplication

def get_jwt_token(client_id, client_secret, tenant_id="5b973f99-77df-4beb-b27d-aa0c70b8482c"):
    """
    Obtain JWT token using client credentials flow.
    
    Args:
        client_id: Azure AD application client ID
        client_secret: Azure AD application client secret
        tenant_id: Azure AD tenant ID (defaults to fixed value)
    
    Returns:
        JWT access token string
    """
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    
    app = ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=authority
    )
    
    # Request token for the API
    scopes = [f"api://{client_id}/.default"]
    
    result = app.acquire_token_for_client(scopes=scopes)
    
    if "access_token" in result:
        return result["access_token"]
    else:
        print(f"Error obtaining token: {result.get('error')}")
        print(f"Error description: {result.get('error_description')}")
        return None

if __name__ == "__main__":
    # Check for environment variables or command line args
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Usage:")
        print("  export CLIENT_ID=your-client-id")
        print("  export CLIENT_SECRET=your-client-secret")
        print("  python get-jwt-token.py")
        print("\nOr:")
        print("  python get-jwt-token.py <client_id> <client_secret>")
        
        if len(sys.argv) >= 3:
            client_id = sys.argv[1]
            client_secret = sys.argv[2]
        else:
            sys.exit(1)
    
    token = get_jwt_token(client_id, client_secret)
    
    if token:
        print(f"\nJWT Token obtained successfully!")
        print(f"\nToken (copy this to Postman environment):")
        print(f"{token}")
        print(f"\nToken length: {len(token)} characters")
    else:
        print("\nFailed to obtain token")
        sys.exit(1)