"""
Spotify client wrapper for the web backend.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class SpotifyClient:
    """Spotify API client wrapper."""
    
    def __init__(self, access_token: str, refresh_token: str, client_id: str, client_secret: str):
        """Initialize Spotify client with user tokens."""
        self.token_info = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': 0  # Will be handled by spotipy
        }
        
        self.auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://localhost:3000/auth/spotify/callback",
            scope="user-library-read playlist-read-private user-follow-read"
        )
        
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
        self.sp.auth_manager.token_info = self.token_info
    
    def get_liked_songs(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get user's liked songs."""
        try:
            songs = []
            results = self.sp.current_user_saved_tracks(limit=50)
            
            while results:
                for item in results["items"]:
                    track = item["track"]
                    track_info = {
                        "spotify_id": track["id"],
                        "name": track["name"],
                        "artists": [artist["name"] for artist in track["artists"]],
                        "album": track["album"]["name"],
                        "duration_ms": track["duration_ms"],
                        "release_date": track["album"]["release_date"],
                        "popularity": track["popularity"],
                        "explicit": track["explicit"],
                        "added_at": item["added_at"],
                        "external_urls": track["external_urls"],
                        "isrc": track.get("external_ids", {}).get("isrc"),
                    }
                    songs.append(track_info)
                    
                    if limit and len(songs) >= limit:
                        return songs[:limit]
                
                # Get next batch
                if results["next"]:
                    results = self.sp.next(results)
                else:
                    break
            
            logger.info(f"Retrieved {len(songs)} liked songs")
            return songs
            
        except Exception as e:
            logger.error(f"Error getting liked songs: {e}")
            raise
    
    def get_followed_artists(self) -> List[Dict[str, Any]]:
        """Get user's followed artists."""
        try:
            artists = []
            results = self.sp.current_user_followed_artists(limit=50)
            
            while results and results["artists"]:
                for artist in results["artists"]["items"]:
                    artist_info = {
                        "spotify_id": artist["id"],
                        "name": artist["name"],
                        "genres": artist["genres"],
                        "popularity": artist["popularity"],
                        "followers": artist["followers"]["total"],
                        "external_urls": artist["external_urls"],
                        "images": artist["images"],
                    }
                    artists.append(artist_info)
                
                # Check if there are more results
                if results["artists"]["next"]:
                    results = self.sp.next(results["artists"])
                else:
                    break
            
            logger.info(f"Retrieved {len(artists)} followed artists")
            return artists
            
        except Exception as e:
            logger.error(f"Error getting followed artists: {e}")
            raise
    
    def get_playlists(self, playlist_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Get user's playlists."""
        try:
            playlists = []
            
            if playlist_ids:
                # Get specific playlists
                for playlist_id in playlist_ids:
                    playlist = self.sp.playlist(playlist_id)
                    playlist_info = self._process_playlist(playlist)
                    playlists.append(playlist_info)
            else:
                # Get all user playlists
                results = self.sp.current_user_playlists(limit=50)
                user_id = self.sp.current_user()["id"]
                
                while results:
                    for playlist in results["items"]:
                        # Skip playlists not owned by user
                        if playlist["owner"]["id"] != user_id:
                            continue
                        
                        playlist_info = self._process_playlist(playlist)
                        playlists.append(playlist_info)
                    
                    if results["next"]:
                        results = self.sp.next(results)
                    else:
                        break
            
            logger.info(f"Retrieved {len(playlists)} playlists")
            return playlists
            
        except Exception as e:
            logger.error(f"Error getting playlists: {e}")
            raise
    
    def _process_playlist(self, playlist: Dict[str, Any]) -> Dict[str, Any]:
        """Process a playlist and get its tracks."""
        try:
            # Get playlist tracks
            tracks = []
            track_results = self.sp.playlist_tracks(playlist["id"], limit=100)
            
            while track_results:
                for item in track_results["items"]:
                    if item["track"] and item["track"]["id"]:  # Skip local files and None tracks
                        track = item["track"]
                        track_info = {
                            "spotify_id": track["id"],
                            "name": track["name"],
                            "artists": [artist["name"] for artist in track["artists"]],
                            "album": track["album"]["name"],
                            "duration_ms": track["duration_ms"],
                            "added_at": item["added_at"],
                            "added_by": item["added_by"]["id"] if item["added_by"] else None,
                        }
                        tracks.append(track_info)
                
                if track_results["next"]:
                    track_results = self.sp.next(track_results)
                else:
                    break
            
            playlist_info = {
                "spotify_id": playlist["id"],
                "name": playlist["name"],
                "description": playlist["description"],
                "public": playlist["public"],
                "collaborative": playlist["collaborative"],
                "followers": playlist.get("followers", {}).get("total", 0),
                "track_count": len(tracks),
                "tracks": tracks,
                "external_urls": playlist["external_urls"],
                "images": playlist.get("images", []),
            }
            
            return playlist_info
            
        except Exception as e:
            logger.error(f"Error processing playlist {playlist.get('id')}: {e}")
            raise