"""
Pydantic schemas for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid


# Base schemas
class UserBase(BaseModel):
    """Base user schema."""
    pass


class UserCreate(UserBase):
    """User creation schema."""
    pass


class UserResponse(UserBase):
    """User response schema."""
    id: uuid.UUID
    created_at: datetime
    last_active: datetime
    spotify_connected: bool = False
    ytmusic_connected: bool = False
    
    class Config:
        from_attributes = True


# Session schemas
class SessionCreate(BaseModel):
    """Session creation request."""
    pass


class SessionResponse(BaseModel):
    """Session creation response."""
    session_id: str
    expires_in: int = 86400


class SessionStatus(BaseModel):
    """Session status response."""
    spotify_connected: bool
    ytmusic_connected: bool
    last_sync: Optional[datetime] = None


# Auth schemas
class SpotifyAuthUrl(BaseModel):
    """Spotify auth URL response."""
    auth_url: str


class SpotifyCallback(BaseModel):
    """Spotify OAuth callback request."""
    code: str
    state: str


class YTMusicDeviceCode(BaseModel):
    """YouTube Music device code response."""
    user_code: str
    verification_url: str
    expires_in: int


class YTMusicPollRequest(BaseModel):
    """YouTube Music OAuth poll request."""
    session_id: str


class YTMusicPollResponse(BaseModel):
    """YouTube Music OAuth poll response."""
    status: str  # 'pending', 'success', 'expired'


# Sync schemas
class SyncOptions(BaseModel):
    """Sync options configuration."""
    liked_songs: bool = False
    playlists: List[str] = Field(default_factory=list)
    artists: bool = False


class SyncJobCreate(BaseModel):
    """Sync job creation request."""
    session_id: str
    sync_options: SyncOptions


class SyncJobResponse(BaseModel):
    """Sync job creation response."""
    job_id: str


class SyncProgress(BaseModel):
    """Sync progress data."""
    stage: str
    current: int
    total: int = 0
    message: str = ""
    updated_at: datetime


class SyncJobStatus(BaseModel):
    """Sync job status response."""
    job_id: str
    status: str
    progress: Optional[SyncProgress] = None
    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SyncResultItem(BaseModel):
    """Individual sync result."""
    id: uuid.UUID
    category: str
    spotify_item: Dict[str, Any]
    ytmusic_match: Optional[Dict[str, Any]] = None
    match_confidence: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime


class SyncJobDetails(SyncJobStatus):
    """Detailed sync job information with results."""
    results: List[SyncResultItem] = Field(default_factory=list)


# Generic responses
class SuccessResponse(BaseModel):
    """Generic success response."""
    status: str = "success"
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Generic error response."""
    detail: str