from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # OAuth Configuration
    oauth_client_id: str
    oauth_client_secret: str
    oauth_domain: str
    oauth_callback_url: str = "http://localhost:8000/auth/callback"
    
    # OAuth URLs (can be customized for different providers)
    oauth_authorize_url: str = ""
    oauth_token_url: str = ""
    oauth_userinfo_url: str = ""
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Application Configuration
    app_host: str = "localhost"
    app_port: int = 8000
    app_debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def get_oauth_urls(self):
        """
        Generate OAuth URLs based on domain.
        Override this method or set URLs directly for custom providers.
        """
        if not self.oauth_authorize_url:
            self.oauth_authorize_url = f"https://{self.oauth_domain}/authorize"
        if not self.oauth_token_url:
            self.oauth_token_url = f"https://{self.oauth_domain}/oauth/token"
        if not self.oauth_userinfo_url:
            self.oauth_userinfo_url = f"https://{self.oauth_domain}/userinfo"
        
        return {
            "authorize_url": self.oauth_authorize_url,
            "token_url": self.oauth_token_url,
            "userinfo_url": self.oauth_userinfo_url
        }


settings = Settings()
