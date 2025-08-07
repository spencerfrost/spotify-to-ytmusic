"""
User management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.schemas import UserResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{session_id}", response_model=UserResponse)
async def get_user(session_id: str, db: Session = Depends(get_db)):
    """Get user information by session ID."""
    try:
        user = db.query(User).filter(User.id == session_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            created_at=user.created_at,
            last_active=user.last_active,
            spotify_connected=user.has_valid_spotify_tokens(),
            ytmusic_connected=user.has_valid_ytmusic_tokens()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )