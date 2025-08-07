# Spotify to YouTube Music Sync

A Python tool to sync your Spotify library to YouTube Music, including liked songs, followed artists, saved albums, and playlists.

## 🎵 Features

- **📊 Inventory Your Spotify Library**: Catalog all your Spotify content
- **❤️ Sync Liked Songs**: Transfer your Spotify liked songs to YouTube Music
- **👥 Follow Artists**: Follow your Spotify artists on YouTube Music  
- **📝 Create Playlists**: Recreate your Spotify playlists on YouTube Music
- **🎯 Smart Matching**: Uses fuzzy matching to find the best song matches
- **📈 Progress Tracking**: See detailed sync progress and statistics

## 📋 Prerequisites

- Python 3.7 or higher
- Spotify Developer Account (for API access)
- YouTube Music subscription (recommended for full functionality)
- Chrome or Firefox browser (for YouTube Music authentication)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Set Up Spotify Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Note your `Client ID` and `Client Secret`
4. Add `http://127.0.0.1:8888/callback` as a redirect URI
5. Create a `.env` file:

```bash
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 3. Generate Spotify Inventory

```bash
python inventory.py
```

This will scan your entire Spotify library and create:
- `spotify_inventory_YYYYMMDD_HHMMSS.json` - Complete inventory data
- `spotify_export_YYYYMMDD_HHMMSS_*.csv` - CSV exports for easy viewing

### 4. Set Up YouTube Music Authentication

```bash
python setup_auth.py
```

Follow the interactive instructions to set up YouTube Music authentication. You'll need to:
1. Open YouTube Music in your browser
2. Extract browser request headers using Developer Tools
3. Paste them into the setup script

### 5. Run the Sync

```bash
python youtube_music_sync.py
```

Choose what you want to sync:
- **Option 1**: Liked songs only (good for testing)
- **Option 2**: Followed artists only
- **Option 3**: Playlists only
- **Option 4**: Everything (full sync)
- **Option 5**: Custom selection

## 📁 File Structure

```
spotify-to-ytmusic/
├── inventory.py              # Spotify library scanner
├── youtube_music_sync.py     # Main sync script
├── setup_auth.py            # YouTube Music auth setup
├── requirements.txt         # Python dependencies
├── .env                     # Spotify credentials (you create this)
├── ytmusic_auth.json       # YouTube Music auth (auto-generated)
└── README.md               # This file
```

## ⚙️ Configuration

### Spotify API Scopes

The tool requires these Spotify scopes:
- `user-library-read` - Access liked songs and saved albums
- `playlist-read-private` - Access your playlists
- `user-follow-read` - Access followed artists

### YouTube Music Authentication

The tool uses `ytmusicapi` which requires browser authentication headers. This is more reliable than OAuth for YouTube Music's unofficial API.

## 🎯 How It Works

### Song Matching Algorithm

1. **Search Strategy**: Multiple search queries with different combinations of artist and track names
2. **Fuzzy Matching**: Uses `fuzzywuzzy` to calculate similarity scores
3. **Confidence Thresholds**: Only matches songs with high confidence (>70% similarity)
4. **Multiple Factors**: Considers track name, artist name, and duration for matching

### Rate Limiting

The script includes built-in rate limiting to be respectful to the APIs:
- 1 second between song searches
- 1.5 seconds between artist searches
- 2 seconds between playlist operations

## 📊 What Gets Synced

### ✅ Supported
- ❤️ **Liked Songs** - Matches and likes songs on YouTube Music
- 👥 **Followed Artists** - Subscribes to artists on YouTube Music
- 📝 **Playlists** - Creates playlists and adds matching songs
- 📋 **Playlist Metadata** - Preserves playlist names and descriptions

### ❌ Not Yet Supported
- 💿 **Saved Albums** - YouTube Music doesn't have equivalent functionality
- 🏷️ **Custom Playlist Order** - YouTube Music API limitations
- 📍 **Local Files** - Only works with tracks available on both platforms

## 🔧 Troubleshooting

### Common Issues

1. **"No module named 'ytmusicapi'"**
   ```bash
   pip install -r requirements.txt
   ```

2. **"Authentication failed"**
   - Re-run `python setup_auth.py`
   - Make sure you're logged into YouTube Music
   - Try using a different browser request

3. **"No matches found"**
   - Some songs may not be available on YouTube Music
   - Regional availability differences
   - Check song names for special characters

4. **Rate limiting errors**
   - The script includes delays, but you can increase them if needed
   - YouTube Music may temporarily block rapid requests

### Testing Mode

Start with a small number of songs to test:
```bash
# Test with 10 liked songs
python youtube_music_sync.py
# Choose option 1, then enter 10 when prompted
```

### Debug Mode

For detailed logging, edit the script and change:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Statistics

After sync completion, you'll see a summary:
- Songs matched and liked
- Artists followed
- Playlists created
- Any failures and reasons

## ⚠️ Important Notes

1. **Backup First**: Consider exporting your YouTube Music library before syncing
2. **API Limits**: Both Spotify and YouTube Music have rate limits
3. **Matching Accuracy**: Not all songs will match perfectly between platforms
4. **One-Way Sync**: This is a one-time transfer tool, not a continuous sync
5. **Private Playlists**: Created playlists will be private by default

## 🤝 Contributing

This tool is designed for personal use. If you encounter issues:
1. Check the troubleshooting section
2. Verify your authentication setup
3. Test with a small subset of songs first

## 📜 Legal

This tool uses unofficial APIs and is for personal use only. Respect the terms of service for both Spotify and YouTube Music.

## 🎉 Success Tips

1. **Start Small**: Test with 10-20 songs first
2. **Check Matches**: Review the match quality before full sync
3. **Be Patient**: Large libraries take time to sync
4. **Internet Connection**: Ensure stable internet during sync
5. **Browser Session**: Keep YouTube Music tab open during authentication setup

Happy syncing! 🎵
