// Sync operation types
export interface SyncOptions {
  liked_songs: boolean;
  playlists: string[];
  artists: boolean;
}

export interface SyncProgress {
  stage: string;
  current: number;
  total: number;
  message: string;
  updated_at: string;
}

export interface SyncJobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress?: SyncProgress;
  total_items: number;
  successful_items: number;
  failed_items: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface SyncResultItem {
  id: string;
  category: 'liked_songs' | 'playlists' | 'artists';
  spotify_item: any;
  ytmusic_match?: any;
  match_confidence?: number;
  status: 'success' | 'no_match' | 'error' | 'skipped';
  error_message?: string;
  created_at: string;
}

export interface SyncJobDetails extends SyncJobStatus {
  results: SyncResultItem[];
}