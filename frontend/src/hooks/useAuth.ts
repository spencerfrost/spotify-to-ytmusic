import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Session, SessionStatus } from '@/types/auth';

export function useAuth() {
  const [session, setSession] = useState<Session | null>(null);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = async () => {
    try {
      setLoading(true);
      setError(null);

      // Check for existing session
      const sessionId = localStorage.getItem('sessionId');

      if (sessionId) {
        try {
          const status = await api.get<SessionStatus>(`/auth/session/${sessionId}`);
          setSession({ id: sessionId, expires_in: 86400 });
          setSessionStatus(status);
          return;
        } catch (error) {
          console.warn('Existing session invalid, creating new one');
          localStorage.removeItem('sessionId');
        }
      }

      // Create new session
      const newSession = await api.post<Session>('/auth/session');
      localStorage.setItem('sessionId', newSession.id);
      setSession(newSession);
      
      // Get initial status
      const status = await api.get<SessionStatus>(`/auth/session/${newSession.id}`);
      setSessionStatus(status);

    } catch (error: any) {
      console.error('Failed to initialize session:', error);
      setError(error.message || 'Failed to initialize session');
    } finally {
      setLoading(false);
    }
  };

  const refreshAuth = async () => {
    if (!session) return;
    
    try {
      const status = await api.get<SessionStatus>(`/auth/session/${session.id}`);
      setSessionStatus(status);
    } catch (error: any) {
      console.error('Failed to refresh auth status:', error);
      setError(error.message || 'Failed to refresh auth status');
    }
  };

  return {
    session,
    sessionStatus,
    loading,
    error,
    refreshAuth,
    spotifyConnected: sessionStatus?.spotify_connected || false,
    ytmusicConnected: sessionStatus?.ytmusic_connected || false,
  };
}