/**
 * useLawyerDashboard Hook
 * 003-role-based-ui Feature - US2
 *
 * Hook for fetching and managing lawyer dashboard data.
 */

'use client';
import { logger } from '@/lib/logger';

import { useState, useEffect, useCallback } from 'react';
import {
  getLawyerDashboard,
  getLawyerAnalytics,
  LawyerDashboardResponse,
  LawyerAnalyticsResponse,
} from '@/lib/api/lawyer';

export interface UseLawyerDashboardResult {
  /** Dashboard data (alias for compatibility) */
  data: LawyerDashboardResponse | null;
  /** Dashboard data */
  dashboard: LawyerDashboardResponse | null;
  /** Analytics data */
  analytics: LawyerAnalyticsResponse | null;
  /** Loading state */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Refresh dashboard data */
  refresh: () => Promise<void>;
  /** Refresh analytics data */
  refreshAnalytics: () => Promise<void>;
}

/**
 * useLawyerDashboard - Fetch and manage lawyer dashboard data
 *
 * Usage:
 * ```tsx
 * const { dashboard, analytics, isLoading, error, refresh } = useLawyerDashboard();
 *
 * if (isLoading) return <Loading />;
 * if (error) return <Error message={error} />;
 *
 * return <Dashboard data={dashboard} />;
 * ```
 */
export function useLawyerDashboard(): UseLawyerDashboardResult {
  const [dashboard, setDashboard] = useState<LawyerDashboardResponse | null>(null);
  const [analytics, setAnalytics] = useState<LawyerAnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await getLawyerDashboard();

      if (response.error) {
        setError(response.error);
        return;
      }

      if (response.data) {
        // Debug: check if recent_cases have valid ids (dev only)
        if (process.env.NODE_ENV === 'development' && response.data.recent_cases) {
          response.data.recent_cases.forEach((c, idx) => {
            if (!c.id) {
              console.warn(`[useLawyerDashboard] recent_cases[${idx}] missing id:`, c);
            }
          });
        }
        setDashboard(response.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '대시보드 데이터를 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchAnalytics = useCallback(async () => {
    try {
      const response = await getLawyerAnalytics();

      if (response.error) {
        logger.error('Analytics fetch error:', response.error);
        return;
      }

      if (response.data) {
        setAnalytics(response.data);
      }
    } catch (err) {
      logger.error('Analytics fetch error:', err);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
    fetchAnalytics();
  }, [fetchDashboard, fetchAnalytics]);

  return {
    data: dashboard,
    dashboard,
    analytics,
    isLoading,
    error,
    refresh: fetchDashboard,
    refreshAnalytics: fetchAnalytics,
  };
}

export default useLawyerDashboard;
