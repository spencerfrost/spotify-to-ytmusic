"""
Configuration management using Pydantic settings.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql://localhost/spotify_ytmusic"
    
    # Spotify OAuth
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:3000/auth/spotify/callback"
    
    # Google/YouTube Music OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # Security
    jwt_secret_key: str = "your-super-secret-jwt-key-change-this"
    encryption_key: str = "your-super-secret-encryption-key-32-chars"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Redis (for caching device codes)
    redis_url: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings