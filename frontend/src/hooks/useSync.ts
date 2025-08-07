import { useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { SyncOptions, SyncJobStatus } from '@/types/sync';

export function useSync() {
  const [currentJob, setCurrentJob] = useState<SyncJobStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startSync = useCallback(async (sessionId: string, options: SyncOptions) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post<{ job_id: string }>('/sync/start', {
        session_id: sessionId,
        sync_options: options,
      });

      // Start polling for job status
      pollJobStatus(response.job_id);
      
      return response.job_id;
    } catch (error: any) {
      console.error('Failed to start sync:', error);
      setError(error.message || 'Failed to start sync');
      setLoading(false);
      throw error;
    }
  }, []);

  const pollJobStatus = useCallback(async (jobId: string) => {
    try {
      const job = await api.get<SyncJobStatus>(`/sync/job/${jobId}`);
      setCurrentJob(job);

      // Continue polling if job is still running
      if (job.status === 'running' || job.status === 'pending') {
        setTimeout(() => pollJobStatus(jobId), 2000);
      } else {
        setLoading(false);
      }
    } catch (error: any) {
      console.error('Failed to get job status:', error);
      setError(error.message || 'Failed to get job status');
      setLoading(false);
    }
  }, []);

  const getJobDetails = useCallback(async (jobId: string) => {
    try {
      const details = await api.get(`/sync/job/${jobId}/details`);
      return details;
    } catch (error: any) {
      console.error('Failed to get job details:', error);
      throw error;
    }
  }, []);

  const getUserJobs = useCallback(async (sessionId: string) => {
    try {
      const jobs = await api.get<SyncJobStatus[]>(`/sync/user/${sessionId}/jobs`);
      return jobs;
    } catch (error: any) {
      console.error('Failed to get user jobs:', error);
      throw error;
    }
  }, []);

  return {
    currentJob,
    loading,
    error,
    startSync,
    getJobDetails,
    getUserJobs,
  };
}