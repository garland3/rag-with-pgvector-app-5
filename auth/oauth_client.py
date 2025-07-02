import httpx
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import secrets
from config import settings


class OAuthClient:
    def __init__(self):
        self.client_id = settings.oauth_client_id
        self.client_secret = settings.oauth_client_secret
        self.callback_url = settings.oauth_callback_url
        self.oauth_urls = settings.get_oauth_urls()
    
    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """
        Generate the OAuth authorization URL and state parameter.
        Returns: (authorization_url, state)
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.callback_url,
            "scope": "openid profile email",
            "state": state,
        }
        
        auth_url = f"{self.oauth_urls['authorize_url']}?{urlencode(params)}"
        return auth_url, state
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token and user info.
        """
        token_data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.callback_url,
        }
        
        async with httpx.AsyncClient() as client:
            # Get access token
            token_response = await client.post(
                self.oauth_urls["token_url"],
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if token_response.status_code != 200:
                raise Exception(f"Token exchange failed: {token_response.text}")
            
            tokens = token_response.json()
            access_token = tokens.get("access_token")
            
            if not access_token:
                raise Exception("No access token received")
            
            # Get user info
            user_info = await self.get_user_info(access_token)
            
            return {
                "tokens": tokens,
                "user_info": user_info
            }
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information using the access token.
        """
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                self.oauth_urls["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise Exception(f"Failed to get user info: {user_response.text}")
            
            return user_response.json()


oauth_client = OAuthClient()
