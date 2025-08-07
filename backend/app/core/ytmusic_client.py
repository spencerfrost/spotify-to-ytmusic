"""
YouTube Music client wrapper for the web backend.
"""

from ytmusicapi import YTMusic
from typing import Dict, List, Any, Optional
from fuzzywuzzy import fuzz
import logging
import re

logger = logging.getLogger(__name__)


class YTMusicClient:
    """YouTube Music API client wrapper."""
    
    def __init__(self, oauth_tokens: Dict[str, Any]):
        """Initialize YouTube Music client with user tokens."""
        try:
            # Create YTMusic instance with OAuth tokens
            self.ytmusic = YTMusic(oauth_tokens)
            logger.info("YouTube Music client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube Music client: {e}")
            raise
    
    def calculate_match_score(self, spotify_track: Dict, ytmusic_track: Dict) -> int:
        """
        Calculate similarity score between Spotify and YouTube Music tracks.
        
        Args:
            spotify_track: Spotify track data
            ytmusic_track: YouTube Music track data
            
        Returns:
            Match score (0-100)
        """
        # Get track info
        spotify_title = spotify_track['name'].lower()
        spotify_artists = [artist.lower() for artist in spotify_track['artists']]
        
        ytmusic_title = ytmusic_track.get('title', '').lower()
        ytmusic_artists = []
        
        # Extract YouTube Music artists
        if 'artists' in ytmusic_track:
            ytmusic_artists = [artist.get('name', '').lower() for artist in ytmusic_track['artists']]
        
        # Calculate title similarity
        title_score = fuzz.ratio(spotify_title, ytmusic_title)
        
        # Calculate artist similarity
        artist_score = 0
        if spotify_artists and ytmusic_artists:
            for sp_artist in spotify_artists:
                for yt_artist in ytmusic_artists:
                    artist_match = fuzz.ratio(sp_artist, yt_artist)
                    artist_score = max(artist_score, artist_match)
        
        # Calculate duration similarity (if available)
        duration_score = 100  # Default if no duration data
        if 'duration_ms' in spotify_track and 'duration_seconds' in ytmusic_track:
            spotify_duration = spotify_track['duration_ms'] / 1000
            ytmusic_duration = int(ytmusic_track['duration_seconds']) if ytmusic_track['duration_seconds'] else 0
            if ytmusic_duration > 0:
                duration_diff = abs(spotify_duration - ytmusic_duration)
                duration_score = max(0, 100 - (duration_diff * 2))
        
        # Weighted average: title is most important, then artist, then duration
        total_score = (title_score * 0.5 + artist_score * 0.4 + duration_score * 0.1)
        return int(total_score)
    
    def search_song(self, spotify_track: Dict) -> Optional[Dict]:
        """
        Search for a Spotify track on YouTube Music.
        
        Args:
            spotify_track: Spotify track data
            
        Returns:
            Best matching YouTube Music track or None
        """
        track_name = spotify_track['name']
        artists = spotify_track['artists']
        primary_artist = artists[0] if artists else "Unknown"
        
        # Clean track name for better matching
        clean_track = re.sub(r'\(.*?\)', '', track_name).strip()  # Remove parentheses
        clean_track = re.sub(r'\[.*?\]', '', clean_track).strip()  # Remove brackets
        clean_track = re.sub(r'\s*-\s*.*$', '', clean_track).strip()  # Remove " - " and after
        
        # Try different search strategies
        search_queries = [
            f"{primary_artist} {clean_track}",
            f"{track_name} {primary_artist}",
            f"{clean_track}",
            track_name
        ]
        
        best_match = None
        best_score = 0
        
        for query in search_queries:
            try:
                logger.debug(f"Searching: {query}")
                results = self.ytmusic.search(query, filter="songs", limit=10)
                
                for result in results:
                    score = self.calculate_match_score(spotify_track, result)
                    if score > best_score and score > 70:  # Minimum confidence threshold
                        best_match = result
                        best_score = score
                        
                if best_match and best_score > 85:  # High confidence match found
                    break
                    
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                continue
                
        if best_match:
            logger.info(f"Match found (score: {best_score}): {best_match.get('title', 'Unknown')}")
        else:
            logger.warning(f"No match found for: {track_name} by {primary_artist}")
            
        return best_match if best_match else None
    
    def rate_song(self, video_id: str, rating: str = "LIKE") -> bool:
        """
        Rate a song on YouTube Music.
        
        Args:
            video_id: YouTube Music video ID
            rating: Rating ('LIKE', 'DISLIKE', 'INDIFFERENT')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.ytmusic.rate_song(video_id, rating)
            logger.info(f"Rated song {video_id}: {rating}")
            return True
        except Exception as e:
            logger.error(f"Failed to rate song {video_id}: {e}")
            return False
    
    def search_artist(self, artist_name: str) -> Optional[Dict]:
        """
        Search for an artist on YouTube Music.
        
        Args:
            artist_name: Name of the artist
            
        Returns:
            Best matching artist or None
        """
        try:
            logger.info(f"Searching for artist: {artist_name}")
            results = self.ytmusic.search(artist_name, filter="artists", limit=5)
            
            # Find best match
            best_match = None
            best_score = 0
            
            for result in results:
                score = fuzz.ratio(artist_name.lower(), result.get('artist', '').lower())
                if score > best_score:
                    best_match = result
                    best_score = score
            
            if best_match and best_score > 80:  # High confidence threshold for artists
                logger.info(f"Artist match found (score: {best_score}): {best_match.get('artist', artist_name)}")
                return best_match
            
            logger.warning(f"No good match found for artist: {artist_name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to search for artist '{artist_name}': {e}")
            return None
    
    def subscribe_artist(self, channel_id: str) -> bool:
        """
        Subscribe to an artist on YouTube Music.
        
        Args:
            channel_id: Artist's channel ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.ytmusic.subscribe_artists([channel_id])
            logger.info(f"Subscribed to artist: {channel_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to artist {channel_id}: {e}")
            return False
    
    def create_playlist(self, title: str, description: str = "", privacy_status: str = "PRIVATE") -> Optional[str]:
        """
        Create a playlist on YouTube Music.
        
        Args:
            title: Playlist title
            description: Playlist description
            privacy_status: Privacy status ('PRIVATE', 'PUBLIC', 'UNLISTED')
            
        Returns:
            Playlist ID if successful, None otherwise
        """
        try:
            playlist_id = self.ytmusic.create_playlist(
                title=title,
                description=description,
                privacy_status=privacy_status
            )
            logger.info(f"Created playlist: {title}")
            return playlist_id
        except Exception as e:
            logger.error(f"Failed to create playlist '{title}': {e}")
            return None
    
    def add_songs_to_playlist(self, playlist_id: str, video_ids: List[str]) -> int:
        """
        Add songs to a YouTube Music playlist.
        
        Args:
            playlist_id: YouTube Music playlist ID
            video_ids: List of video IDs to add
            
        Returns:
            Number of successfully added songs
        """
        try:
            if not video_ids:
                return 0
            
            # Add songs in batches to avoid API limits
            batch_size = 50
            added_count = 0
            
            for i in range(0, len(video_ids), batch_size):
                batch = video_ids[i:i + batch_size]
                try:
                    self.ytmusic.add_playlist_items(playlist_id, batch)
                    added_count += len(batch)
                    logger.info(f"Added batch of {len(batch)} songs to playlist")
                except Exception as e:
                    logger.error(f"Failed to add batch to playlist: {e}")
                    
            return added_count
            
        except Exception as e:
            logger.error(f"Failed to add songs to playlist: {e}")
            return 0