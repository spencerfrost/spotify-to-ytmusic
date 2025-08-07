# Spotify to YouTube Music Sync - Web App

A modern web application for syncing your Spotify library to YouTube Music, featuring real-time progress tracking, OAuth authentication, and a beautiful React frontend.

## 🎵 Features

- **🔐 Secure OAuth**: Spotify Web API and YouTube Music TV device flow authentication
- **📊 Real-time Progress**: WebSocket-powered live updates during sync operations
- **❤️ Sync Liked Songs**: Transfer your Spotify liked songs to YouTube Music
- **👥 Follow Artists**: Follow your Spotify artists on YouTube Music  
- **📝 Create Playlists**: Recreate your Spotify playlists on YouTube Music
- **🎯 Smart Matching**: Advanced fuzzy matching algorithms for accurate song detection
- **📈 Detailed Results**: Complete sync history with match confidence scores
- **🌙 Modern UI**: Beautiful, responsive interface with dark/light mode support

## 🏗️ Architecture

```
React Frontend → FastAPI Backend → PostgreSQL Database → Spotify/YTMusic APIs
     ↓              ↓                    ↓
  ShadCN UI     Background Tasks    Session Storage
  WebSockets    OAuth Handling      Sync Results
```

## 🚀 Tech Stack

**Frontend**: React + TypeScript + Tailwind CSS + ShadCN UI
- Modern component architecture with type safety
- Beautiful, accessible UI components
- Real-time progress updates via WebSockets
- Responsive design

**Backend**: FastAPI + Python + PostgreSQL
- Async support for long-running sync operations
- Automatic API documentation at `/docs`
- WebSocket support for real-time progress
- Background task processing

**Database**: PostgreSQL
- User session management
- OAuth token storage (secure)
- Sync job tracking and history
- Detailed results storage

## 📁 Project Structure

```
spotify-ytmusic-web/
├── frontend/                     # React + TypeScript + Tailwind + ShadCN
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # ShadCN components
│   │   │   ├── auth/            # Authentication components
│   │   │   └── sync/            # Sync operation components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # API client and utilities
│   │   └── types/               # TypeScript type definitions
│   ├── package.json
│   └── vite.config.ts
├── backend/                      # FastAPI + PostgreSQL
│   ├── app/
│   │   ├── main.py              # FastAPI app initialization
│   │   ├── api/                 # API endpoints
│   │   ├── core/                # Core business logic
│   │   ├── models/              # Database models
│   │   └── utils/               # Utilities and config
│   └── requirements.txt
├── deploy/                       # Deployment configurations
│   ├── vercel.json              # Frontend deployment
│   ├── railway.toml             # Backend deployment
│   ├── Dockerfile               # Container configuration
│   └── docker-compose.yml       # Local development
└── README.md
```

## 🛠️ Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (optional for basic testing)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

4. **Start the backend**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at http://localhost:8000 with automatic docs at http://localhost:8000/docs

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

   The app will be available at http://localhost:3000

### Using Docker (Recommended)

1. **Set up environment variables**:
   ```bash
   cp backend/.env.example backend/.env
   # Add your Spotify and Google API credentials
   ```

2. **Start all services**:
   ```bash
   docker-compose -f deploy/docker-compose.yml up -d
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🔑 API Configuration

### Spotify App Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add `http://localhost:3000/auth/spotify/callback` to redirect URIs
4. Note your Client ID and Client Secret

### Google/YouTube Music Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials (Desktop Application)
5. Note your Client ID and Client Secret

### Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql://localhost/spotify_ytmusic
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET_KEY=your-jwt-secret-key
ENCRYPTION_KEY=your-32-character-encryption-key
CORS_ORIGINS=["http://localhost:3000"]
```

## 🎯 How It Works

### Authentication Flow

1. **Session Creation**: App creates a unique session for each user
2. **Spotify OAuth**: Standard OAuth2 web flow with automatic token refresh
3. **YouTube Music Auth**: Google OAuth2 TV device flow for better UX
4. **Token Storage**: Secure, encrypted storage of OAuth tokens

### Sync Process

1. **Background Tasks**: Long-running sync operations handled asynchronously
2. **Real-time Updates**: WebSocket connection provides live progress updates
3. **Smart Matching**: Multi-strategy search with fuzzy matching algorithms
4. **Result Tracking**: Detailed success/failure tracking for every item

### Sync Categories

- **❤️ Liked Songs**: Matches and likes songs on YouTube Music
- **👥 Artists**: Subscribes to artists on YouTube Music
- **📝 Playlists**: Creates playlists and adds matching songs

## 🚀 Deployment

### Frontend (Vercel)

1. **Connect your repository to Vercel**
2. **Set build settings**:
   - Build Command: `cd frontend && npm run build`
   - Output Directory: `frontend/dist`
   - Install Command: `cd frontend && npm install`

3. **Environment Variables**:
   ```
   VITE_API_URL=https://your-backend-url.railway.app
   ```

### Backend (Railway)

1. **Connect your repository to Railway**
2. **Add PostgreSQL service**
3. **Environment Variables**:
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   CORS_ORIGINS=["https://your-frontend-domain.vercel.app"]
   ```

## 📊 API Endpoints

### Authentication
- `POST /auth/session` - Create user session
- `GET /auth/session/{session_id}` - Get session status
- `GET /auth/spotify/url` - Get Spotify auth URL
- `POST /auth/spotify/callback` - Handle Spotify callback
- `POST /auth/ytmusic/start` - Start YouTube Music device flow
- `POST /auth/ytmusic/poll` - Poll for auth completion

### Sync Operations
- `POST /sync/start` - Start sync operation
- `GET /sync/job/{job_id}` - Get job status
- `GET /sync/job/{job_id}/details` - Get detailed results
- `WS /ws/sync/{job_id}` - Real-time progress updates

## 🔒 Security Features

- **Token Encryption**: All OAuth tokens encrypted before database storage
- **Session Management**: Secure session handling with automatic expiration
- **CORS Protection**: Restricted to configured frontend domains
- **Input Validation**: Comprehensive request validation with Pydantic
- **Error Handling**: Secure error responses that don't expose internals

## 🎉 Success Tips

1. **Start Small**: Test with a few songs/artists first
2. **Stable Connection**: Ensure stable internet during sync operations
3. **API Limits**: Respect rate limits - the app handles this automatically
4. **Match Quality**: Review match confidence scores in detailed results
5. **Retry Failed**: Use the detailed results to identify and retry failed items

## 📜 Legal & Privacy

- **Personal Use**: This tool is for personal use only
- **API Compliance**: Respects Terms of Service for both Spotify and YouTube Music
- **Data Privacy**: No data shared with third parties
- **Local Storage**: All user data stored locally or in your chosen database

## 🤝 Contributing

This is a personal project template. Feel free to fork and customize for your own use!

## 📞 Support

For setup issues:
1. Check the troubleshooting section above
2. Verify your API credentials
3. Ensure all services are running
4. Check browser console for frontend errors
5. Check server logs for backend errors

---

**Happy syncing! 🎵**
