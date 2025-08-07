import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SpotifyAuth } from './SpotifyAuth';
import { YTMusicAuth } from './YTMusicAuth';
import { CheckCircle, Circle } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

export function AuthStepper() {
  const { session, spotifyConnected, ytmusicConnected, refreshAuth } = useAuth();

  if (!session) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Initializing session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Spotify to YouTube Music Sync</h1>
        <p className="text-muted-foreground">
          Connect your accounts to start syncing your music library
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            {spotifyConnected ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <Circle className="h-5 w-5 text-muted-foreground" />
            )}
            <CardTitle>Connect Spotify</CardTitle>
            {spotifyConnected && (
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                Connected
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!spotifyConnected ? (
            <SpotifyAuth sessionId={session.id} onSuccess={refreshAuth} />
          ) : (
            <p className="text-green-600">✓ Spotify account connected successfully</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            {ytmusicConnected ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <Circle className="h-5 w-5 text-muted-foreground" />
            )}
            <CardTitle>Connect YouTube Music</CardTitle>
            {ytmusicConnected && (
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                Connected
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!ytmusicConnected ? (
            <YTMusicAuth sessionId={session.id} onSuccess={refreshAuth} />
          ) : (
            <p className="text-green-600">✓ YouTube Music connected successfully</p>
          )}
        </CardContent>
      </Card>

      {spotifyConnected && ytmusicConnected && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="text-center">
              <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-green-800 mb-2">
                Ready to Sync!
              </h3>
              <p className="text-green-700">
                Both accounts are connected. You can now start syncing your music library.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}