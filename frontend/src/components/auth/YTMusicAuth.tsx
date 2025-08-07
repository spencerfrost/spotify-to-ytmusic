import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api';
import { YTMusicDeviceCode, YTMusicPollResponse } from '@/types/auth';
import { Copy, ExternalLink, Loader2 } from 'lucide-react';

interface YTMusicAuthProps {
  sessionId: string;
  onSuccess?: () => void;
}

export function YTMusicAuth({ sessionId, onSuccess }: YTMusicAuthProps) {
  const [deviceCode, setDeviceCode] = useState<YTMusicDeviceCode | null>(null);
  const [status, setStatus] = useState<'idle' | 'waiting' | 'success' | 'error'>('idle');
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startOAuth = async () => {
    try {
      setError(null);
      const response = await api.post<YTMusicDeviceCode>('/auth/ytmusic/start', {
        session_id: sessionId,
      });

      setDeviceCode(response);
      setStatus('waiting');
      setPolling(true);

      // Open verification URL
      window.open(response.verification_url, '_blank');

      // Start polling
      pollForAuth();
    } catch (error: any) {
      console.error('YTMusic auth error:', error);
      setError(error.message || 'Failed to start YouTube Music authentication');
      setStatus('error');
    }
  };

  const pollForAuth = async () => {
    if (!polling) return;

    try {
      const response = await api.post<YTMusicPollResponse>('/auth/ytmusic/poll', {
        session_id: sessionId,
      });

      if (response.status === 'success') {
        setStatus('success');
        setPolling(false);
        onSuccess?.();
      } else if (response.status === 'pending' && polling) {
        setTimeout(pollForAuth, 2000); // Poll every 2 seconds
      } else if (response.status === 'expired') {
        setStatus('error');
        setError('Authorization expired. Please try again.');
        setPolling(false);
      }
    } catch (error: any) {
      console.error('YTMusic poll error:', error);
      setError(error.message || 'Failed to check authorization status');
      setStatus('error');
      setPolling(false);
    }
  };

  const copyUserCode = () => {
    if (deviceCode) {
      navigator.clipboard.writeText(deviceCode.user_code);
    }
  };

  useEffect(() => {
    return () => {
      setPolling(false);
    };
  }, []);

  if (status === 'success') {
    return (
      <div className="p-3 text-sm text-green-600 bg-green-50 border border-green-200 rounded-md">
        ✓ YouTube Music connected successfully!
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Connect your YouTube Music account to sync your library.
      </p>

      {error && (
        <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
          {error}
        </div>
      )}

      {status === 'idle' && (
        <Button onClick={startOAuth} className="w-full bg-red-600 hover:bg-red-700">
          Connect YouTube Music
        </Button>
      )}

      {status === 'waiting' && deviceCode && (
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
            <div className="space-y-3">
              <p className="text-sm font-medium">Complete authorization on Google's website:</p>
              
              <div className="flex items-center gap-2">
                <Input 
                  value={deviceCode.user_code} 
                  readOnly 
                  className="font-mono text-center text-lg"
                />
                <Button variant="outline" size="sm" onClick={copyUserCode}>
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
              
              <Button 
                variant="outline" 
                onClick={() => window.open(deviceCode.verification_url, '_blank')}
                className="w-full"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Open Google Authorization
              </Button>
            </div>
          </div>

          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Waiting for authorization...
          </div>
        </div>
      )}

      {status === 'error' && (
        <Button 
          onClick={() => {
            setStatus('idle');
            setError(null);
            setDeviceCode(null);
          }}
          variant="outline"
          className="w-full"
        >
          Try Again
        </Button>
      )}
    </div>
  );
}