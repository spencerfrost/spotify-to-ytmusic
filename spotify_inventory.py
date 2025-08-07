#!/usr/bin/env python3
"""
Spotify Library Inventory Script
Fetches and catalogs all Spotify library content for transfer planning.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import csv
from datetime import datetime
import os
from typing import Dict, Any
from dotenv import load_dotenv


class SpotifyInventory:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://127.0.0.1:8888/callback",
    ):
        """Initialize Spotify client with OAuth authentication."""
        self.scope = "user-library-read playlist-read-private user-follow-read"
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=self.scope,
            )
        )
        self.inventory = {
            "metadata": {
                "scan_date": datetime.now().isoformat(),
                "user_id": None,
                "display_name": None,
            },
            "liked_songs": [],
            "playlists": [],
            "followed_artists": [],
            "saved_albums": [],
        }

    def get_user_info(self):
        """Get basic user information."""
        user = self.sp.current_user()
        self.inventory["metadata"]["user_id"] = user["id"]
        self.inventory["metadata"]["display_name"] = user["display_name"]
        print(f"📱 Scanning library for: {user['display_name']} ({user['id']})")

    def fetch_liked_songs(self):
        """Fetch all liked/saved songs."""
        print("🎵 Fetching liked songs...")
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
                self.inventory["liked_songs"].append(track_info)

            # Get next batch
            if results["next"]:
                results = self.sp.next(results)
            else:
                break

        print(f"   ✓ Found {len(self.inventory['liked_songs'])} liked songs")

    def fetch_playlists(self):
        """Fetch all user playlists and their contents."""
        print("📝 Fetching playlists...")
        results = self.sp.current_user_playlists(limit=50)

        while results:
            for playlist in results["items"]:
                # Skip playlists not owned by user (followed playlists)
                if playlist["owner"]["id"] != self.inventory["metadata"]["user_id"]:
                    continue

                print(f"   📋 Processing playlist: {playlist['name']}")

                # Get playlist tracks
                tracks = []
                track_results = self.sp.playlist_tracks(playlist["id"], limit=100)

                while track_results:
                    for item in track_results["items"]:
                        if (
                            item["track"] and item["track"]["id"]
                        ):  # Skip local files and None tracks
                            track = item["track"]
                            track_info = {
                                "spotify_id": track["id"],
                                "name": track["name"],
                                "artists": [
                                    artist["name"] for artist in track["artists"]
                                ],
                                "album": track["album"]["name"],
                                "duration_ms": track["duration_ms"],
                                "added_at": item["added_at"],
                                "added_by": (
                                    item["added_by"]["id"] if item["added_by"] else None
                                ),
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
                self.inventory["playlists"].append(playlist_info)

            if results["next"]:
                results = self.sp.next(results)
            else:
                break

        total_playlist_tracks = sum(
            len(p["tracks"]) for p in self.inventory["playlists"]
        )
        print(
            f"   ✓ Found {len(self.inventory['playlists'])} playlists with {total_playlist_tracks} total tracks"
        )

    def fetch_followed_artists(self):
        """Fetch all followed artists."""
        print("👥 Fetching followed artists...")
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
                self.inventory["followed_artists"].append(artist_info)

            # Check if there are more results
            if results["artists"]["next"]:
                results = self.sp.next(results["artists"])
            else:
                break

        print(f"   ✓ Found {len(self.inventory['followed_artists'])} followed artists")

    def fetch_saved_albums(self):
        """Fetch all saved albums."""
        print("💿 Fetching saved albums...")
        results = self.sp.current_user_saved_albums(limit=50)

        while results:
            for item in results["items"]:
                album = item["album"]
                album_info = {
                    "spotify_id": album["id"],
                    "name": album["name"],
                    "artists": [artist["name"] for artist in album["artists"]],
                    "release_date": album["release_date"],
                    "total_tracks": album["total_tracks"],
                    "album_type": album["album_type"],
                    "added_at": item["added_at"],
                    "external_urls": album["external_urls"],
                    "images": album["images"],
                }
                self.inventory["saved_albums"].append(album_info)

            if results["next"]:
                results = self.sp.next(results)
            else:
                break

        print(f"   ✓ Found {len(self.inventory['saved_albums'])} saved albums")

    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of the inventory."""
        total_playlist_tracks = sum(
            len(p["tracks"]) for p in self.inventory["playlists"]
        )
        unique_artists = set()

        # Collect unique artists from liked songs
        for song in self.inventory["liked_songs"]:
            unique_artists.update(song["artists"])

        # Collect unique artists from playlists
        for playlist in self.inventory["playlists"]:
            for track in playlist["tracks"]:
                unique_artists.update(track["artists"])

        summary = {
            "liked_songs_count": len(self.inventory["liked_songs"]),
            "playlists_count": len(self.inventory["playlists"]),
            "total_playlist_tracks": total_playlist_tracks,
            "followed_artists_count": len(self.inventory["followed_artists"]),
            "saved_albums_count": len(self.inventory["saved_albums"]),
            "unique_artists_in_library": len(unique_artists),
            "largest_playlist": (
                max(self.inventory["playlists"], key=lambda x: x["track_count"])["name"]
                if self.inventory["playlists"]
                else None
            ),
            "largest_playlist_size": (
                max(self.inventory["playlists"], key=lambda x: x["track_count"])[
                    "track_count"
                ]
                if self.inventory["playlists"]
                else 0
            ),
        }

        return summary

    def save_inventory(self, filename: str = None):
        """Save inventory to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"spotify_inventory_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.inventory, f, indent=2, ensure_ascii=False)

        print(f"💾 Inventory saved to: {filename}")
        return filename

    def export_to_csv(self, base_filename: str = None):
        """Export inventory data to CSV files for easy viewing."""
        if not base_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"spotify_export_{timestamp}"

        # Export liked songs
        if self.inventory["liked_songs"]:
            with open(
                f"{base_filename}_liked_songs.csv", "w", newline="", encoding="utf-8"
            ) as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "name",
                        "artists",
                        "album",
                        "duration_ms",
                        "release_date",
                        "spotify_id",
                    ],
                )
                writer.writeheader()
                for song in self.inventory["liked_songs"]:
                    row = song.copy()
                    row["artists"] = "; ".join(song["artists"])
                    writer.writerow({k: row[k] for k in writer.fieldnames})

        # Export playlists summary
        if self.inventory["playlists"]:
            with open(
                f"{base_filename}_playlists.csv", "w", newline="", encoding="utf-8"
            ) as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "name",
                        "track_count",
                        "public",
                        "collaborative",
                        "followers",
                        "spotify_id",
                    ],
                )
                writer.writeheader()
                for playlist in self.inventory["playlists"]:
                    writer.writerow({k: playlist[k] for k in writer.fieldnames})

        # Export followed artists
        if self.inventory["followed_artists"]:
            with open(
                f"{base_filename}_artists.csv", "w", newline="", encoding="utf-8"
            ) as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "name",
                        "genres",
                        "popularity",
                        "followers",
                        "spotify_id",
                    ],
                )
                writer.writeheader()
                for artist in self.inventory["followed_artists"]:
                    row = artist.copy()
                    row["genres"] = "; ".join(artist["genres"])
                    writer.writerow({k: row[k] for k in writer.fieldnames})

        print(f"📊 CSV exports saved with prefix: {base_filename}")


def main():
    """Main function to run the inventory scan."""
    # Load environment variables from .env file
    load_dotenv()
    
    print("🎵 Spotify Library Inventory Tool")
    print("=" * 40)

    # Check for credentials
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ Missing Spotify credentials!")
        print("Please set environment variables:")
        print("   SPOTIFY_CLIENT_ID=your_client_id")
        print("   SPOTIFY_CLIENT_SECRET=your_client_secret")
        print("\nOr get them from: https://developer.spotify.com/dashboard")
        return

    try:
        # Initialize inventory
        inventory = SpotifyInventory(client_id, client_secret)

        # Get user info
        inventory.get_user_info()
        print()

        # Fetch all data
        inventory.fetch_liked_songs()
        inventory.fetch_playlists()
        inventory.fetch_followed_artists()
        inventory.fetch_saved_albums()

        print("\n📊 Library Summary:")
        print("=" * 40)

        summary = inventory.generate_summary()
        for key, value in summary.items():
            formatted_key = key.replace("_", " ").title()
            print(f"{formatted_key}: {value}")

        print("\n💾 Saving data...")
        json_file = inventory.save_inventory()
        inventory.export_to_csv()

        print(f"\n✅ Inventory complete! Check {json_file} for full data.")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have valid Spotify credentials and internet connection.")


if __name__ == "__main__":
    main()
