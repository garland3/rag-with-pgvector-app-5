from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # OAuth Configuration
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_domain: Optional[str] = None
    oauth_callback_url: str = "http://localhost:8000/auth/callback"
    
    # OAuth URLs (can be customized for different providers)
    oauth_authorize_url: str = ""
    oauth_token_url: str = ""
    oauth_userinfo_url: str = ""
    
    # JWT Configuration
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Application Configuration
    app_host: str = "localhost"
    app_port: int = 8000
    app_debug: bool = True
    
    # Database URL
    database_url: str = "postgresql://postgres:password@localhost:5432/your_app_db"
    
    # Gemini API Key
    gemini_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
    
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
