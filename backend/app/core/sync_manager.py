"""
Background sync manager for handling sync operations.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.spotify_client import SpotifyClient
from app.core.ytmusic_client import YTMusicClient
from app.models.sync import SyncJob, SyncResult
from app.models.user import User
from app.api.websocket import send_job_progress
from app.utils.config import get_settings

logger = logging.getLogger(__name__)


class SyncManager:
    """Background sync manager for handling sync operations."""
    
    def __init__(self, job_id: str):
        """Initialize sync manager with job ID."""
        self.job_id = job_id
        self.settings = get_settings()
        self.db = SessionLocal()
        
        # Get job and user
        self.job = self.db.query(SyncJob).filter(SyncJob.id == job_id).first()
        if not self.job:
            raise ValueError(f"Job {job_id} not found")
        
        self.user = self.job.user
        if not self.user:
            raise ValueError(f"User not found for job {job_id}")
        
        # Initialize API clients
        self.spotify_client = None
        self.ytmusic_client = None
        
    def __del__(self):
        """Clean up database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    def _init_spotify_client(self):
        """Initialize Spotify client."""
        try:
            self.spotify_client = SpotifyClient(
                access_token=self.user.spotify_access_token,
                refresh_token=self.user.spotify_refresh_token,
                client_id=self.settings.spotify_client_id,
                client_secret=self.settings.spotify_client_secret
            )
            logger.info("Spotify client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
            raise
    
    def _init_ytmusic_client(self):
        """Initialize YouTube Music client."""
        try:
            self.ytmusic_client = YTMusicClient(self.user.ytmusic_oauth_tokens)
            logger.info("YouTube Music client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube Music client: {e}")
            raise
    
    async def _update_progress(self, stage: str, current: int, total: int = 0, message: str = ""):
        """Update job progress and send WebSocket update."""
        try:
            # Update database
            self.job.update_progress(stage, current, message)
            if total > 0:
                self.job.total_items = total
            self.db.commit()
            
            # Send WebSocket update
            progress_data = {
                "job_id": self.job_id,
                "status": self.job.status,
                "progress": {
                    "stage": stage,
                    "current": current,
                    "total": total,
                    "message": message
                },
                "total_items": self.job.total_items,
                "successful_items": self.job.successful_items,
                "failed_items": self.job.failed_items
            }
            
            await send_job_progress(self.job_id, progress_data)
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
    
    def _create_sync_result(self, category: str, spotify_item: Dict, ytmusic_match: Dict = None, 
                          status: str = "success", error_message: str = None, match_confidence: float = None):
        """Create a sync result record."""
        try:
            result = SyncResult(
                job_id=self.job.id,
                category=category,
                spotify_item=spotify_item,
                ytmusic_match=ytmusic_match,
                match_confidence=match_confidence,
                status=status,
                error_message=error_message
            )
            self.db.add(result)
            
            # Update job counters
            if status == "success":
                self.job.successful_items += 1
            else:
                self.job.failed_items += 1
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating sync result: {e}")
    
    async def sync_liked_songs(self):
        """Sync Spotify liked songs to YouTube Music."""
        try:
            await self._update_progress("liked_songs", 0, message="Getting liked songs from Spotify...")
            
            # Get Spotify liked songs
            liked_songs = self.spotify_client.get_liked_songs()
            total_songs = len(liked_songs)
            
            await self._update_progress("liked_songs", 0, total_songs, f"Found {total_songs} liked songs")
            
            for i, song in enumerate(liked_songs):
                try:
                    # Search for match on YouTube Music
                    ytmusic_match = self.ytmusic_client.search_song(song)
                    
                    if ytmusic_match:
                        # Calculate match confidence
                        confidence = self.ytmusic_client.calculate_match_score(song, ytmusic_match) / 100.0
                        
                        # Try to like the song
                        video_id = ytmusic_match.get('videoId')
                        if video_id and self.ytmusic_client.rate_song(video_id, 'LIKE'):
                            self._create_sync_result(
                                category="liked_songs",
                                spotify_item=song,
                                ytmusic_match=ytmusic_match,
                                status="success",
                                match_confidence=confidence
                            )
                        else:
                            self._create_sync_result(
                                category="liked_songs",
                                spotify_item=song,
                                ytmusic_match=ytmusic_match,
                                status="error",
                                error_message="Failed to like song on YouTube Music",
                                match_confidence=confidence
                            )
                    else:
                        self._create_sync_result(
                            category="liked_songs",
                            spotify_item=song,
                            status="no_match",
                            error_message="No matching song found on YouTube Music"
                        )
                    
                    # Update progress
                    await self._update_progress(
                        "liked_songs", 
                        i + 1, 
                        total_songs, 
                        f"Processed {i + 1}/{total_songs} songs"
                    )
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing song {song.get('name', 'Unknown')}: {e}")
                    self._create_sync_result(
                        category="liked_songs",
                        spotify_item=song,
                        status="error",
                        error_message=str(e)
                    )
                    
        except Exception as e:
            logger.error(f"Error syncing liked songs: {e}")
            raise
    
    async def sync_artists(self):
        """Sync Spotify followed artists to YouTube Music."""
        try:
            await self._update_progress("artists", 0, message="Getting followed artists from Spotify...")
            
            # Get Spotify followed artists
            followed_artists = self.spotify_client.get_followed_artists()
            total_artists = len(followed_artists)
            
            await self._update_progress("artists", 0, total_artists, f"Found {total_artists} followed artists")
            
            for i, artist in enumerate(followed_artists):
                try:
                    # Search for artist on YouTube Music
                    ytmusic_match = self.ytmusic_client.search_artist(artist['name'])
                    
                    if ytmusic_match:
                        # Try to subscribe to the artist
                        channel_id = ytmusic_match.get('browseId')
                        if channel_id and self.ytmusic_client.subscribe_artist(channel_id):
                            self._create_sync_result(
                                category="artists",
                                spotify_item=artist,
                                ytmusic_match=ytmusic_match,
                                status="success"
                            )
                        else:
                            self._create_sync_result(
                                category="artists",
                                spotify_item=artist,
                                ytmusic_match=ytmusic_match,
                                status="error",
                                error_message="Failed to subscribe to artist on YouTube Music"
                            )
                    else:
                        self._create_sync_result(
                            category="artists",
                            spotify_item=artist,
                            status="no_match",
                            error_message="No matching artist found on YouTube Music"
                        )
                    
                    # Update progress
                    await self._update_progress(
                        "artists", 
                        i + 1, 
                        total_artists, 
                        f"Processed {i + 1}/{total_artists} artists"
                    )
                    
                    # Rate limiting
                    await asyncio.sleep(1.5)
                    
                except Exception as e:
                    logger.error(f"Error processing artist {artist.get('name', 'Unknown')}: {e}")
                    self._create_sync_result(
                        category="artists",
                        spotify_item=artist,
                        status="error",
                        error_message=str(e)
                    )
                    
        except Exception as e:
            logger.error(f"Error syncing artists: {e}")
            raise
    
    async def sync_playlists(self, playlist_ids: List[str] = None):
        """Sync Spotify playlists to YouTube Music."""
        try:
            await self._update_progress("playlists", 0, message="Getting playlists from Spotify...")
            
            # Get Spotify playlists
            playlists = self.spotify_client.get_playlists(playlist_ids)
            total_playlists = len(playlists)
            
            await self._update_progress("playlists", 0, total_playlists, f"Found {total_playlists} playlists")
            
            for i, playlist in enumerate(playlists):
                try:
                    playlist_name = playlist['name']
                    playlist_description = f"Synced from Spotify. Original description: {playlist.get('description', '')}"
                    tracks = playlist.get('tracks', [])
                    
                    # Create playlist on YouTube Music
                    playlist_id = self.ytmusic_client.create_playlist(
                        title=playlist_name,
                        description=playlist_description
                    )
                    
                    if playlist_id:
                        # Find matching songs and collect video IDs
                        video_ids = []
                        for j, track in enumerate(tracks):
                            ytmusic_match = self.ytmusic_client.search_song(track)
                            if ytmusic_match and ytmusic_match.get('videoId'):
                                video_ids.append(ytmusic_match['videoId'])
                            
                            # Mini progress update for large playlists
                            if j % 10 == 0:
                                await self._update_progress(
                                    "playlists", 
                                    i, 
                                    total_playlists, 
                                    f"Processing playlist {i+1}/{total_playlists}: finding matches {j+1}/{len(tracks)}"
                                )
                            
                            await asyncio.sleep(0.5)  # Rate limiting
                        
                        # Add songs to playlist
                        added_count = self.ytmusic_client.add_songs_to_playlist(playlist_id, video_ids)
                        
                        self._create_sync_result(
                            category="playlists",
                            spotify_item=playlist,
                            ytmusic_match={"playlist_id": playlist_id, "songs_added": added_count},
                            status="success"
                        )
                        
                        logger.info(f"Created playlist '{playlist_name}' with {added_count}/{len(tracks)} songs")
                    else:
                        self._create_sync_result(
                            category="playlists",
                            spotify_item=playlist,
                            status="error",
                            error_message="Failed to create playlist on YouTube Music"
                        )
                    
                    # Update progress
                    await self._update_progress(
                        "playlists", 
                        i + 1, 
                        total_playlists, 
                        f"Processed {i + 1}/{total_playlists} playlists"
                    )
                    
                    # Rate limiting between playlists
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing playlist {playlist.get('name', 'Unknown')}: {e}")
                    self._create_sync_result(
                        category="playlists",
                        spotify_item=playlist,
                        status="error",
                        error_message=str(e)
                    )
                    
        except Exception as e:
            logger.error(f"Error syncing playlists: {e}")
            raise
    
    async def run_sync(self):
        """Run the sync operation based on job options."""
        try:
            # Update job status
            self.job.update_status("running")
            self.db.commit()
            
            # Initialize API clients
            self._init_spotify_client()
            self._init_ytmusic_client()
            
            sync_options = self.job.sync_options
            
            # Sync liked songs
            if sync_options.get("liked_songs"):
                await self.sync_liked_songs()
            
            # Sync followed artists
            if sync_options.get("artists"):
                await self.sync_artists()
            
            # Sync playlists
            if sync_options.get("playlists"):
                playlist_ids = sync_options["playlists"] if isinstance(sync_options["playlists"], list) else None
                await self.sync_playlists(playlist_ids)
            
            # Mark job as completed
            self.job.update_status("completed")
            self.db.commit()
            
            await self._update_progress("completed", self.job.total_items, self.job.total_items, "Sync completed successfully!")
            
        except Exception as e:
            logger.error(f"Sync job {self.job_id} failed: {e}")
            self.job.update_status("failed", error=str(e))
            self.db.commit()
            
            await self._update_progress("failed", 0, 0, f"Sync failed: {str(e)}")
            raise


async def run_sync_task(job_id: str):
    """Background task to run sync operation."""
    try:
        sync_manager = SyncManager(job_id)
        await sync_manager.run_sync()
        logger.info(f"Sync job {job_id} completed successfully")
    except Exception as e:
        logger.error(f"Sync job {job_id} failed: {e}")
        raise