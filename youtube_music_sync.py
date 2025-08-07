#!/usr/bin/env python3
"""
YouTube Music Sync Script
Syncs Spotify inventory data to YouTube Music using ytmusicapi.
"""

import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ytmusicapi import YTMusic
from fuzzywuzzy import fuzz

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of matching a Spotify track to YouTube Music."""
    spotify_track: Dict
    ytmusic_track: Optional[Dict]
    match_score: int
    matched: bool
    action_taken: str = ""


class YouTubeMusicSync:
    def __init__(self, auth_file: str = "browser.json"):
        """
        Initialize YouTube Music sync client.
        
        Args:
            auth_file: Path to ytmusicapi authentication file
        """
        try:
            self.ytmusic = YTMusic(auth_file)
            logger.info("✅ YouTube Music client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize YouTube Music client: {e}")
            raise
            
        self.stats = {
            "songs_searched": 0,
            "songs_matched": 0,
            "songs_liked": 0,
            "songs_failed": 0,
            "artists_searched": 0,
            "artists_followed": 0,
            "playlists_created": 0,
            "playlist_songs_added": 0
        }

    def load_spotify_inventory(self, inventory_file: str) -> Dict:
        """Load Spotify inventory from JSON file."""
        try:
            with open(inventory_file, 'r', encoding='utf-8') as f:
                inventory = json.load(f)
            logger.info(f"📂 Loaded Spotify inventory: {inventory_file}")
            return inventory
        except Exception as e:
            logger.error(f"❌ Failed to load inventory: {e}")
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

    def search_youtube_music(self, spotify_track: Dict) -> Optional[Dict]:
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
        import re
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
                logger.debug(f"🔍 Searching: {query}")
                results = self.ytmusic.search(query, filter="songs", limit=10)
                
                for result in results:
                    score = self.calculate_match_score(spotify_track, result)
                    if score > best_score and score > 70:  # Minimum confidence threshold
                        best_match = result
                        best_score = score
                        
                if best_match and best_score > 85:  # High confidence match found
                    break
                    
            except Exception as e:
                logger.warning(f"⚠️ Search failed for query '{query}': {e}")
                continue
                
        if best_match:
            logger.info(f"✅ Match found (score: {best_score}): {best_match.get('title', 'Unknown')}")
        else:
            logger.warning(f"❌ No match found for: {track_name} by {primary_artist}")
            
        return best_match

    def like_song(self, ytmusic_track: Dict) -> bool:
        """
        Like a song on YouTube Music.
        
        Args:
            ytmusic_track: YouTube Music track data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            video_id = ytmusic_track.get('videoId')
            if not video_id:
                logger.warning("⚠️ No video ID found for track")
                return False
                
            # Use rate_song to like the track
            response = self.ytmusic.rate_song(video_id, 'LIKE')
            logger.info(f"❤️ Liked: {ytmusic_track.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to like song: {e}")
            return False

    def sync_liked_songs(self, spotify_inventory: Dict, limit: Optional[int] = None) -> List[MatchResult]:
        """
        Sync Spotify liked songs to YouTube Music.
        
        Args:
            spotify_inventory: Spotify inventory data
            limit: Maximum number of songs to process (for testing)
            
        Returns:
            List of match results
        """
        logger.info("🎵 Starting liked songs sync...")
        
        liked_songs = spotify_inventory.get('liked_songs', [])
        if limit:
            liked_songs = liked_songs[:limit]
            
        results = []
        
        for i, spotify_track in enumerate(liked_songs, 1):
            logger.info(f"📈 Processing {i}/{len(liked_songs)}: {spotify_track['name']} by {', '.join(spotify_track['artists'])}")
            
            self.stats['songs_searched'] += 1
            
            # Search for match
            ytmusic_match = self.search_youtube_music(spotify_track)
            
            match_result = MatchResult(
                spotify_track=spotify_track,
                ytmusic_track=ytmusic_match,
                match_score=self.calculate_match_score(spotify_track, ytmusic_match) if ytmusic_match else 0,
                matched=ytmusic_match is not None
            )
            
            if ytmusic_match:
                self.stats['songs_matched'] += 1
                # Try to like the song
                if self.like_song(ytmusic_match):
                    self.stats['songs_liked'] += 1
                    match_result.action_taken = "liked"
                else:
                    self.stats['songs_failed'] += 1
                    match_result.action_taken = "like_failed"
            else:
                self.stats['songs_failed'] += 1
                match_result.action_taken = "not_found"
            
            results.append(match_result)
            
            # Rate limiting - be nice to the API
            time.sleep(1)
            
        return results

    def search_and_follow_artist(self, artist_name: str) -> bool:
        """
        Search for and follow an artist on YouTube Music.
        
        Args:
            artist_name: Name of the artist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🔍 Searching for artist: {artist_name}")
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
                channel_id = best_match.get('browseId')
                if channel_id:
                    # Use subscribe_artists method
                    self.ytmusic.subscribe_artists([channel_id])
                    logger.info(f"✅ Followed artist: {best_match.get('artist', artist_name)}")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Failed to follow artist '{artist_name}': {e}")
            
        return False

    def sync_followed_artists(self, spotify_inventory: Dict) -> int:
        """
        Sync Spotify followed artists to YouTube Music.
        
        Args:
            spotify_inventory: Spotify inventory data
            
        Returns:
            Number of successfully followed artists
        """
        logger.info("👥 Starting followed artists sync...")
        
        followed_artists = spotify_inventory.get('followed_artists', [])
        followed_count = 0
        
        for i, artist in enumerate(followed_artists, 1):
            artist_name = artist['name']
            logger.info(f"📈 Processing {i}/{len(followed_artists)}: {artist_name}")
            
            self.stats['artists_searched'] += 1
            
            if self.search_and_follow_artist(artist_name):
                followed_count += 1
                self.stats['artists_followed'] += 1
                
            # Rate limiting
            time.sleep(1.5)
            
        logger.info(f"✅ Successfully followed {followed_count}/{len(followed_artists)} artists")
        return followed_count

    def create_playlist(self, playlist_name: str, description: str = "") -> Optional[str]:
        """
        Create a playlist on YouTube Music.
        
        Args:
            playlist_name: Name of the playlist
            description: Playlist description
            
        Returns:
            Playlist ID if successful, None otherwise
        """
        try:
            playlist_id = self.ytmusic.create_playlist(
                title=playlist_name,
                description=description,
                privacy_status="PRIVATE"
            )
            logger.info(f"📋 Created playlist: {playlist_name}")
            return playlist_id
        except Exception as e:
            logger.error(f"❌ Failed to create playlist '{playlist_name}': {e}")
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
            if video_ids:
                # Add songs in batches to avoid API limits
                batch_size = 50
                added_count = 0
                
                for i in range(0, len(video_ids), batch_size):
                    batch = video_ids[i:i + batch_size]
                    try:
                        self.ytmusic.add_playlist_items(playlist_id, batch)
                        added_count += len(batch)
                        logger.info(f"✅ Added batch of {len(batch)} songs to playlist")
                        time.sleep(1)  # Rate limiting between batches
                    except Exception as e:
                        logger.error(f"❌ Failed to add batch to playlist: {e}")
                        
                return added_count
        except Exception as e:
            logger.error(f"❌ Failed to add songs to playlist: {e}")
        return 0

    def sync_playlists(self, spotify_inventory: Dict, limit_per_playlist: Optional[int] = None) -> int:
        """
        Sync Spotify playlists to YouTube Music.
        
        Args:
            spotify_inventory: Spotify inventory data
            limit_per_playlist: Maximum songs per playlist (for testing)
            
        Returns:
            Number of successfully created playlists
        """
        logger.info("📝 Starting playlists sync...")
        
        playlists = spotify_inventory.get('playlists', [])
        created_count = 0
        
        for playlist in playlists:
            playlist_name = playlist['name']
            playlist_description = f"Synced from Spotify. Original description: {playlist.get('description', '')}"
            tracks = playlist.get('tracks', [])
            
            if limit_per_playlist:
                tracks = tracks[:limit_per_playlist]
            
            logger.info(f"📋 Processing playlist: {playlist_name} ({len(tracks)} tracks)")
            
            # Create playlist
            playlist_id = self.create_playlist(playlist_name, playlist_description)
            if not playlist_id:
                continue
                
            self.stats['playlists_created'] += 1
                
            # Find matching songs
            video_ids = []
            for j, track in enumerate(tracks, 1):
                logger.info(f"   🔍 Finding match {j}/{len(tracks)}: {track['name']}")
                ytmusic_match = self.search_youtube_music(track)
                if ytmusic_match and ytmusic_match.get('videoId'):
                    video_ids.append(ytmusic_match['videoId'])
                time.sleep(0.5)  # Rate limiting
                
            # Add songs to playlist
            if video_ids:
                added_count = self.add_songs_to_playlist(playlist_id, video_ids)
                self.stats['playlist_songs_added'] += added_count
                logger.info(f"✅ Added {added_count}/{len(tracks)} songs to '{playlist_name}'")
            else:
                logger.warning(f"⚠️ No matching songs found for playlist '{playlist_name}'")
                
            # Rate limiting between playlists
            time.sleep(2)
            
        logger.info(f"✅ Successfully created {created_count}/{len(playlists)} playlists")
        return created_count

    def print_summary(self):
        """Print sync summary statistics."""
        print("\n" + "="*60)
        print("📊 YOUTUBE MUSIC SYNC SUMMARY")
        print("="*60)
        print(f"🔍 Songs searched: {self.stats['songs_searched']}")
        print(f"✅ Songs matched: {self.stats['songs_matched']}")
        print(f"❤️ Songs liked: {self.stats['songs_liked']}")
        print(f"❌ Songs failed: {self.stats['songs_failed']}")
        print(f"🔍 Artists searched: {self.stats['artists_searched']}")
        print(f"👥 Artists followed: {self.stats['artists_followed']}")
        print(f"📋 Playlists created: {self.stats['playlists_created']}")
        print(f"🎵 Playlist songs added: {self.stats['playlist_songs_added']}")
        
        if self.stats['songs_searched'] > 0:
            match_rate = (self.stats['songs_matched'] / self.stats['songs_searched']) * 100
            print(f"📈 Match rate: {match_rate:.1f}%")
            
        print("="*60)


def main():
    """Main function to run the YouTube Music sync."""
    print("🎵 YouTube Music Sync Tool")
    print("=" * 40)
    
    # Check if ytmusicapi auth file exists
    auth_file = "browser.json"
    try:
        sync = YouTubeMusicSync(auth_file)
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\n📋 Setup Instructions:")
        print("1. Run: ytmusicapi browser")
        print("2. Follow the browser authentication instructions")
        print("3. This will create browser.json with your credentials")
        return
    
    # Load Spotify inventory
    try:
        # Look for the most recent inventory file
        import os
        inventory_files = [f for f in os.listdir('.') if f.startswith('spotify_inventory_') and f.endswith('.json')]
        if not inventory_files:
            print("❌ No Spotify inventory file found!")
            print("Run the inventory.py script first to generate the inventory.")
            return
        
        latest_inventory = max(inventory_files)
        inventory = sync.load_spotify_inventory(latest_inventory)
        print(f"📂 Using inventory: {latest_inventory}")
        
    except Exception as e:
        print(f"❌ Failed to load inventory: {e}")
        return
    
    print(f"\n📊 Spotify Library Summary:")
    print(f"   🎵 Liked songs: {len(inventory.get('liked_songs', []))}")
    print(f"   📋 Playlists: {len(inventory.get('playlists', []))}")
    print(f"   👥 Followed artists: {len(inventory.get('followed_artists', []))}")
    print(f"   💿 Saved albums: {len(inventory.get('saved_albums', []))}")
    
    print("\n🎯 What would you like to sync?")
    print("1. Liked songs only (recommended for testing)")
    print("2. Followed artists only")
    print("3. Playlists only")
    print("4. Everything (full sync)")
    print("5. Custom selection")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    try:
        if choice == "1":
            limit = input("How many songs to sync? (press Enter for all): ").strip()
            limit = int(limit) if limit else None
            sync.sync_liked_songs(inventory, limit=limit)
            
        elif choice == "2":
            sync.sync_followed_artists(inventory)
            
        elif choice == "3":
            limit = input("Max songs per playlist? (press Enter for all): ").strip()
            limit = int(limit) if limit else None
            sync.sync_playlists(inventory, limit_per_playlist=limit)
            
        elif choice == "4":
            print("⚠️ Full sync will take a long time. Continue? (y/N)")
            if input().lower() == 'y':
                sync.sync_liked_songs(inventory)
                sync.sync_followed_artists(inventory)
                sync.sync_playlists(inventory)
            else:
                print("Cancelled.")
                return
                
        elif choice == "5":
            print("Custom sync options:")
            if input("Sync liked songs? (y/N): ").lower() == 'y':
                limit = input("How many songs? (press Enter for all): ").strip()
                limit = int(limit) if limit else None
                sync.sync_liked_songs(inventory, limit=limit)
            if input("Sync followed artists? (y/N): ").lower() == 'y':
                sync.sync_followed_artists(inventory)
            if input("Sync playlists? (y/N): ").lower() == 'y':
                limit = input("Max songs per playlist? (press Enter for all): ").strip()
                limit = int(limit) if limit else None
                sync.sync_playlists(inventory, limit_per_playlist=limit)
        else:
            print("Invalid choice.")
            return
            
    except KeyboardInterrupt:
        print("\n⚠️ Sync interrupted by user.")
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        logger.exception("Full error details:")
    finally:
        sync.print_summary()


if __name__ == "__main__":
    main()
