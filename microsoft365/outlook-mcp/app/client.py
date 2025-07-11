"""Client module for Microsoft Graph API authentication and client creation."""

import os
from typing import List
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from azure.core.credentials import AccessToken
from azure.core.credentials_async import AsyncTokenCredential

class StaticTokenCredential(AsyncTokenCredential):
    """Static token credential for Microsoft Graph authentication."""
    
    def __init__(self, token: str):
        self.token = token
    
    async def get_token(self, *scopes, **kwargs) -> AccessToken:
        """Get access token."""
        return AccessToken(self.token, 0)  # 0 means no expiration tracking


def create_client(scopes: List[str], token: str) -> GraphServiceClient:
    """Create a Microsoft Graph client with the given scopes."""
    
    credential = StaticTokenCredential(token)
    return GraphServiceClient(credentials=credential, scopes=scopes) 