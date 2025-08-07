"""
Sync job and results database models.
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
from typing import Optional


class SyncJob(Base):
    """Sync job tracking model."""
    
    __tablename__ = "sync_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(String(20), nullable=False, default="pending")
    
    # Sync configuration
    sync_options = Column(JSONB, nullable=False)
    
    # Progress tracking
    progress = Column(JSONB, default={})
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    # Results summary
    total_items = Column(Integer, default=0)
    successful_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Relationship
    user = relationship("User")
    results = relationship("SyncResult", back_populates="job", cascade="all, delete-orphan")
    
    def update_status(self, status: str, error: Optional[str] = None):
        """Update job status."""
        self.status = status
        if error:
            self.error_message = error
        if status == "running" and not self.started_at:
            self.started_at = datetime.utcnow()
        elif status in ["completed", "failed", "cancelled"]:
            self.completed_at = datetime.utcnow()
    
    def update_progress(self, stage: str, current: int, message: str = ""):
        """Update job progress."""
        if not self.progress:
            self.progress = {}
        
        self.progress.update({
            "stage": stage,
            "current": current,
            "message": message,
            "updated_at": datetime.utcnow().isoformat()
        })


class SyncResult(Base):
    """Detailed sync results for individual items."""
    
    __tablename__ = "sync_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("sync_jobs.id", ondelete="CASCADE"))
    
    # Item details
    category = Column(String(20), nullable=False)  # 'liked_songs', 'playlists', 'artists'
    spotify_item = Column(JSONB, nullable=False)   # Original Spotify data
    
    # Match results
    ytmusic_match = Column(JSONB)                  # Found YouTube Music item (if any)
    match_confidence = Column(Float)               # Fuzzy match score (0-1)
    
    # Status
    status = Column(String(20), nullable=False)    # 'success', 'no_match', 'error', 'skipped'
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    job = relationship("SyncJob", back_populates="results")