"""
FastAPI main application module.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio
import json
from typing import Dict, Any

from app.api import auth, sync, users, websocket
from app.core.database import engine, Base
from app.utils.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Spotify to YouTube Music Sync",
    description="Web app for syncing Spotify library to YouTube Music",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
@app.on_event("startup")
async def startup_event():
    """Initialize database and perform startup tasks."""
    try:
        # Create database tables (skip if database is not available)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning(f"Database not available during startup: {e}")
        logger.info("Application will continue without database for testing")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": "1.0.0"}

# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(sync.router, prefix="/sync", tags=["sync"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        self.active_connections[job_id] = websocket
        logger.info(f"WebSocket connected for job: {job_id}")

    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            logger.info(f"WebSocket disconnected for job: {job_id}")

    async def send_progress(self, job_id: str, data: Dict[str, Any]):
        if job_id in self.active_connections:
            try:
                await self.active_connections[job_id].send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                self.disconnect(job_id)

manager = ConnectionManager()

# WebSocket endpoint for sync progress
@app.websocket("/ws/sync/{job_id}")
async def websocket_sync_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time sync progress updates."""
    await manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive and send periodic updates
            await asyncio.sleep(1)
            # Progress updates will be sent from the sync tasks via manager.send_progress()
    except WebSocketDisconnect:
        manager.disconnect(job_id)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )