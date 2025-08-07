"""
WebSocket API endpoints for real-time communication.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.sync import SyncJob
import json
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        self.active_connections[job_id] = websocket
        logger.info(f"WebSocket connected for job: {job_id}")

    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            logger.info(f"WebSocket disconnected for job: {job_id}")

    async def send_progress(self, job_id: str, data: dict):
        if job_id in self.active_connections:
            try:
                await self.active_connections[job_id].send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                self.disconnect(job_id)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/sync/{job_id}")
async def websocket_sync_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time sync progress updates."""
    await manager.connect(websocket, job_id)
    
    try:
        # Get database session
        db = next(get_db())
        
        while True:
            # Fetch current job status
            job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
            if not job:
                await websocket.send_text(json.dumps({"error": "Job not found"}))
                break
            
            # Send progress update
            progress_data = {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress or {},
                "total_items": job.total_items,
                "successful_items": job.successful_items,
                "failed_items": job.failed_items,
                "error_message": job.error_message
            }
            
            await websocket.send_text(json.dumps(progress_data))
            
            # Break if job is completed
            if job.status in ["completed", "failed", "cancelled"]:
                break
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        manager.disconnect(job_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(job_id)


# Function to send progress updates from background tasks
async def send_job_progress(job_id: str, progress_data: dict):
    """Send progress update to WebSocket clients."""
    await manager.send_progress(job_id, progress_data)