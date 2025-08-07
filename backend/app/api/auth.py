"""
Authentication API endpoints for Spotify and YouTube Music OAuth.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, AppConfig
from app.models.schemas import (
    SessionCreate, SessionResponse, SessionStatus,
    SpotifyAuthUrl, SpotifyCallback, 
    YTMusicDeviceCode, YTMusicPollRequest, YTMusicPollResponse,
    SuccessResponse
)
from app.utils.config import get_settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
import requests
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory cache for device codes (in production, use Redis)
device_code_cache: Dict[str, Dict[str, Any]] = {}


@router.post("/session", response_model=SessionResponse)
async def create_session(db: Session = Depends(get_db)):
    """Create a new user session."""
    try:
        user = User()
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return SessionResponse(
            session_id=str(user.id),
            expires_in=86400  # 24 hours
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get("/session/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str, db: Session = Depends(get_db)):
    """Get session authentication status."""
    try:
        user = db.query(User).filter(User.id == session_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Update last active
        user.last_active = datetime.utcnow()
        db.commit()
        
        return SessionStatus(
            spotify_connected=user.has_valid_spotify_tokens(),
            ytmusic_connected=user.has_valid_ytmusic_tokens(),
            last_sync=None  # TODO: Get from sync jobs
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session status"
        )


@router.get("/spotify/url", response_model=SpotifyAuthUrl)
async def get_spotify_auth_url(session_id: str):
    """Get Spotify OAuth authorization URL."""
    try:
        scope = "user-library-read playlist-read-private user-follow-read"
        
        auth_manager = SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope=scope,
            state=session_id
        )
        
        auth_url = auth_manager.get_authorize_url()
        return SpotifyAuthUrl(auth_url=auth_url)
        
    except Exception as e:
        logger.error(f"Error generating Spotify auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Spotify auth URL"
        )


@router.post("/spotify/callback", response_model=SuccessResponse)
async def spotify_callback(callback: SpotifyCallback, db: Session = Depends(get_db)):
    """Handle Spotify OAuth callback."""
    try:
        # Get user from state (session_id)
        user = db.query(User).filter(User.id == callback.state).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid session"
            )
        
        # Exchange code for tokens
        auth_manager = SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            state=callback.state
        )
        
        token_info = auth_manager.get_access_token(callback.code)
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for tokens"
            )
        
        # Store tokens
        expires_at = datetime.utcnow() + timedelta(seconds=token_info['expires_in'])
        user.store_spotify_tokens(
            access_token=token_info['access_token'],
            refresh_token=token_info['refresh_token'],
            expires_at=expires_at
        )
        
        db.commit()
        
        return SuccessResponse(message="Spotify connected successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Spotify callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process Spotify callback"
        )


@router.post("/ytmusic/start", response_model=YTMusicDeviceCode)
async def start_ytmusic_oauth(request: YTMusicPollRequest):
    """Start YouTube Music OAuth device flow."""
    try:
        # Use Google OAuth2 device flow
        device_code_url = "https://oauth2.googleapis.com/device/code"
        
        data = {
            'client_id': settings.google_client_id,
            'scope': 'https://www.googleapis.com/auth/youtube'
        }
        
        response = requests.post(device_code_url, data=data)
        response.raise_for_status()
        device_response = response.json()
        
        # Cache device code data
        device_code_cache[request.session_id] = {
            'device_code': device_response['device_code'],
            'user_code': device_response['user_code'],
            'verification_url': device_response['verification_url'],
            'expires_in': device_response['expires_in'],
            'interval': device_response.get('interval', 5),
            'created_at': time.time()
        }
        
        return YTMusicDeviceCode(
            user_code=device_response['user_code'],
            verification_url=device_response['verification_url'],
            expires_in=device_response['expires_in']
        )
        
    except Exception as e:
        logger.error(f"Error starting YTMusic OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start YouTube Music authentication"
        )


@router.post("/ytmusic/poll", response_model=YTMusicPollResponse)
async def poll_ytmusic_oauth(request: YTMusicPollRequest, db: Session = Depends(get_db)):
    """Poll for YouTube Music OAuth completion."""
    try:
        # Check if device code exists
        if request.session_id not in device_code_cache:
            return YTMusicPollResponse(status="expired")
        
        device_data = device_code_cache[request.session_id]
        
        # Check if expired
        if time.time() - device_data['created_at'] > device_data['expires_in']:
            del device_code_cache[request.session_id]
            return YTMusicPollResponse(status="expired")
        
        # Poll for token
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            'client_id': settings.google_client_id,
            'client_secret': settings.google_client_secret,
            'device_code': device_data['device_code'],
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
        }
        
        response = requests.post(token_url, data=data)
        token_response = response.json()
        
        if response.status_code == 200:
            # Success - got tokens
            user = db.query(User).filter(User.id == request.session_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            # Store tokens
            expires_at = datetime.utcnow() + timedelta(seconds=token_response['expires_in'])
            user.store_ytmusic_tokens(
                tokens=token_response,
                expires_at=expires_at
            )
            
            db.commit()
            
            # Clean up cache
            del device_code_cache[request.session_id]
            
            return YTMusicPollResponse(status="success")
            
        elif token_response.get('error') == 'authorization_pending':
            return YTMusicPollResponse(status="pending")
        else:
            # Error or expired
            del device_code_cache[request.session_id]
            return YTMusicPollResponse(status="expired")
            
    except Exception as e:
        logger.error(f"Error polling YTMusic OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to poll YouTube Music authentication"
        )