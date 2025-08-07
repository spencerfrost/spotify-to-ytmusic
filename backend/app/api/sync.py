"""
Sync operation API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.sync import SyncJob, SyncResult
from app.models.schemas import (
    SyncJobCreate, SyncJobResponse, SyncJobStatus, SyncJobDetails,
    SyncResultItem, SuccessResponse
)
from app.core.sync_manager import run_sync_task
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/start", response_model=SyncJobResponse)
async def start_sync(
    sync_request: SyncJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new sync operation."""
    try:
        # Get user
        user = db.query(User).filter(User.id == sync_request.session_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if user has valid tokens
        if not user.has_valid_spotify_tokens():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Spotify authentication required"
            )
        
        if not user.has_valid_ytmusic_tokens():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="YouTube Music authentication required"
            )
        
        # Create sync job
        sync_job = SyncJob(
            user_id=user.id,
            sync_options=sync_request.sync_options.dict(),
            status="pending"
        )
        db.add(sync_job)
        db.commit()
        db.refresh(sync_job)
        
        # Start background task
        background_tasks.add_task(run_sync_task, str(sync_job.id))
        
        logger.info(f"Started sync job {sync_job.id} for user {user.id}")
        
        return SyncJobResponse(job_id=str(sync_job.id))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start sync operation"
        )


@router.get("/job/{job_id}", response_model=SyncJobStatus)
async def get_sync_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get sync job status."""
    try:
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sync job not found"
            )
        
        progress = job.progress or {}
        
        return SyncJobStatus(
            job_id=str(job.id),
            status=job.status,
            progress={
                "stage": progress.get("stage", ""),
                "current": progress.get("current", 0),
                "total": job.total_items,
                "message": progress.get("message", ""),
                "updated_at": progress.get("updated_at", job.created_at)
            } if progress else None,
            total_items=job.total_items,
            successful_items=job.successful_items,
            failed_items=job.failed_items,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sync job status"
        )


@router.get("/job/{job_id}/details", response_model=SyncJobDetails)
async def get_sync_job_details(job_id: str, db: Session = Depends(get_db)):
    """Get detailed sync job information with results."""
    try:
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sync job not found"
            )
        
        # Get results
        results = db.query(SyncResult).filter(SyncResult.job_id == job_id).all()
        
        progress = job.progress or {}
        
        return SyncJobDetails(
            job_id=str(job.id),
            status=job.status,
            progress={
                "stage": progress.get("stage", ""),
                "current": progress.get("current", 0),
                "total": job.total_items,
                "message": progress.get("message", ""),
                "updated_at": progress.get("updated_at", job.created_at)
            } if progress else None,
            total_items=job.total_items,
            successful_items=job.successful_items,
            failed_items=job.failed_items,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at,
            results=[
                SyncResultItem(
                    id=result.id,
                    category=result.category,
                    spotify_item=result.spotify_item,
                    ytmusic_match=result.ytmusic_match,
                    match_confidence=result.match_confidence,
                    status=result.status,
                    error_message=result.error_message,
                    created_at=result.created_at
                )
                for result in results
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync job details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sync job details"
        )


@router.get("/user/{session_id}/jobs", response_model=List[SyncJobStatus])
async def get_user_sync_jobs(session_id: str, db: Session = Depends(get_db)):
    """Get all sync jobs for a user."""
    try:
        user = db.query(User).filter(User.id == session_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        jobs = db.query(SyncJob).filter(SyncJob.user_id == user.id).order_by(SyncJob.created_at.desc()).all()
        
        return [
            SyncJobStatus(
                job_id=str(job.id),
                status=job.status,
                progress={
                    "stage": job.progress.get("stage", "") if job.progress else "",
                    "current": job.progress.get("current", 0) if job.progress else 0,
                    "total": job.total_items,
                    "message": job.progress.get("message", "") if job.progress else "",
                    "updated_at": job.progress.get("updated_at", job.created_at) if job.progress else job.created_at
                },
                total_items=job.total_items,
                successful_items=job.successful_items,
                failed_items=job.failed_items,
                error_message=job.error_message,
                started_at=job.started_at,
                completed_at=job.completed_at
            )
            for job in jobs
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user sync jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user sync jobs"
        )


@router.delete("/job/{job_id}", response_model=SuccessResponse)
async def cancel_sync_job(job_id: str, db: Session = Depends(get_db)):
    """Cancel a sync job (if it's still running)."""
    try:
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sync job not found"
            )
        
        if job.status in ["completed", "failed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel job that is already completed"
            )
        
        # Update job status
        job.update_status("cancelled")
        db.commit()
        
        logger.info(f"Cancelled sync job {job_id}")
        
        return SuccessResponse(message="Sync job cancelled successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling sync job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel sync job"
        )