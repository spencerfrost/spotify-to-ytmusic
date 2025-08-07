"""
User and session database models.
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import uuid
from datetime import datetime
from typing import Optional


class User(Base):
    """User model for managing sessions and OAuth tokens."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=func.now())
    last_active = Column(DateTime, default=func.now())
    
    # Spotify OAuth tokens
    spotify_access_token = Column(Text)
    spotify_refresh_token = Column(Text)
    spotify_token_expires_at = Column(DateTime)
    
    # YouTube Music OAuth tokens
    ytmusic_oauth_tokens = Column(JSONB)
    ytmusic_token_expires_at = Column(DateTime)
    
    # Encrypted storage key
    token_encryption_key = Column(Text)
    
    def has_valid_spotify_tokens(self) -> bool:
        """Check if user has valid Spotify tokens."""
        return (
            self.spotify_access_token is not None and
            self.spotify_refresh_token is not None and
            self.spotify_token_expires_at is not None and
            self.spotify_token_expires_at > datetime.utcnow()
        )
    
    def has_valid_ytmusic_tokens(self) -> bool:
        """Check if user has valid YouTube Music tokens."""
        return (
            self.ytmusic_oauth_tokens is not None and
            self.ytmusic_token_expires_at is not None and
            self.ytmusic_token_expires_at > datetime.utcnow()
        )
    
    def store_spotify_tokens(self, access_token: str, refresh_token: str, expires_at: datetime):
        """Store Spotify OAuth tokens."""
        self.spotify_access_token = access_token
        self.spotify_refresh_token = refresh_token
        self.spotify_token_expires_at = expires_at
        self.last_active = datetime.utcnow()
    
    def store_ytmusic_tokens(self, tokens: dict, expires_at: datetime):
        """Store YouTube Music OAuth tokens."""
        self.ytmusic_oauth_tokens = tokens
        self.ytmusic_token_expires_at = expires_at
        self.last_active = datetime.utcnow()


class AppConfig(Base):
    """Application configuration storage."""
    
    __tablename__ = "app_config"
    
    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())