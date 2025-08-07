import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { SpotifyAuthUrl } from '@/types/auth';

interface SpotifyAuthProps {
  sessionId: string;
  onSuccess?: () => void;
}

export function SpotifyAuth({ sessionId, onSuccess }: SpotifyAuthProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSpotifyAuth = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get Spotify auth URL
      const response = await api.get<SpotifyAuthUrl>(`/auth/spotify/url?session_id=${sessionId}`);
      
      // Open auth URL in new window
      const authWindow = window.open(
        response.auth_url,
        'spotify-auth',
        'width=500,height=600,scrollbars=yes,resizable=yes'
      );

      // Poll for window closure (indicating auth completion)
      const checkClosed = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(checkClosed);
          setLoading(false);
          
          // Give a moment for the callback to process, then call onSuccess
          setTimeout(() => {
            onSuccess?.();
          }, 1000);
        }
      }, 1000);

      // Cleanup if component unmounts
      return () => {
        clearInterval(checkClosed);
        authWindow?.close();
      };

    } catch (error: any) {
      console.error('Spotify auth error:', error);
      setError(error.message || 'Failed to authenticate with Spotify');
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Connect your Spotify account to access your library and playlists.
      </p>
      
      {error && (
        <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
          {error}
        </div>
      )}
      
      <Button 
        onClick={handleSpotifyAuth} 
        disabled={loading}
        className="w-full bg-green-600 hover:bg-green-700"
      >
        {loading ? 'Connecting...' : 'Connect Spotify'}
      </Button>
    </div>
  );
}