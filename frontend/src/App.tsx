import { useState } from 'react';
import { AuthStepper } from '@/components/auth/AuthStepper';
import { useAuth } from '@/hooks/useAuth';
import './index.css';

function App() {
  const { loading, error, spotifyConnected, ytmusicConnected } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-500 mb-4">
            <svg className="h-12 w-12 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {(!spotifyConnected || !ytmusicConnected) ? (
          <AuthStepper />
        ) : (
          <div className="text-center">
            <h1 className="text-3xl font-bold mb-4">Ready to Sync!</h1>
            <p className="text-muted-foreground mb-8">
              Both accounts are connected. Sync functionality coming soon...
            </p>
            
            {/* TODO: Add sync options and progress components */}
            <div className="p-8 border border-dashed border-muted-foreground/25 rounded-lg">
              <p className="text-muted-foreground">
                🚧 Sync interface under construction 🚧
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;