// Authentication types
export interface Session {
  id: string;
  expires_in: number;
}

export interface SessionStatus {
  spotify_connected: boolean;
  ytmusic_connected: boolean;
  last_sync?: string;
}

export interface SpotifyAuthUrl {
  auth_url: string;
}

export interface YTMusicDeviceCode {
  user_code: string;
  verification_url: string;
  expires_in: number;
}

export interface YTMusicPollResponse {
  status: 'pending' | 'success' | 'expired';
}