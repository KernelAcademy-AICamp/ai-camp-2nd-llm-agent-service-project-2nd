/**
 * Lawyer Portal API Client
 * 003-role-based-ui Feature - US2
 *
 * API functions for lawyer dashboard and case management.
 */

import { apiClient, ApiResponse } from './client';

// Types
export interface StatsCardData {
  label: string;
  value: number;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
}

export interface LawyerDashboardStats {
  total_cases: number;
  active_cases: number;
  pending_review: number;
  completed_this_month: number;
  cases_change?: number;
  stats_cards: StatsCardData[];
}

export interface RecentCaseItem {
  id: string;
  title: string;
  status: string;
  client_name?: string;
  updated_at: string;
  evidence_count: number;
  progress: number;
}

export interface CalendarEventItem {
  id: string;
  title: string;
  event_type: string;
  start_time: string;
  case_id?: string;
  case_title?: string;
}

export interface LawyerDashboardResponse {
  stats: LawyerDashboardStats;
  recent_cases: RecentCaseItem[];
  upcoming_events: CalendarEventItem[];
}

export interface CaseStatusDistribution {
  status: string;
  count: number;
  percentage: number;
}

export interface MonthlyStats {
  month: string;
  new_cases: number;
  completed_cases: number;
  evidence_uploaded: number;
}

export interface LawyerAnalyticsResponse {
  status_distribution: CaseStatusDistribution[];
  monthly_stats: MonthlyStats[];
  total_evidence: number;
  avg_case_duration_days: number;
}

/**
 * Get lawyer dashboard data
 * Includes stats, recent cases, and upcoming events
 */
export async function getLawyerDashboard(): Promise<
  ApiResponse<LawyerDashboardResponse>
> {
  return apiClient.get<LawyerDashboardResponse>('/lawyer/dashboard');
}

/**
 * Get lawyer analytics data
 * Includes status distribution, monthly stats, etc.
 */
export async function getLawyerAnalytics(): Promise<
  ApiResponse<LawyerAnalyticsResponse>
> {
  return apiClient.get<LawyerAnalyticsResponse>('/lawyer/analytics');
}

/**
 * Get case list with filters
 */
export interface CaseListFilter {
  status?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface CaseListItem {
  id: string;
  title: string;
  status: string;
  client_name?: string;
  created_at: string;
  updated_at: string;
  evidence_count: number;
  member_count: number;
}

export interface CaseListResponse {
  cases: CaseListItem[];
  total: number;
  page: number;
  limit: number;
}

export async function getLawyerCases(
  filters?: CaseListFilter
): Promise<ApiResponse<CaseListResponse>> {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, String(value));
      }
    });
  }
  const queryString = params.toString();
  const url = queryString ? `/lawyer/cases?${queryString}` : '/lawyer/cases';
  return apiClient.get<CaseListResponse>(url);
}

/**
 * Perform bulk action on cases
 */
export interface BulkActionRequest {
  case_ids: string[];
  action: 'analyze' | 'archive' | 'export';
}

export interface BulkActionResponse {
  success: boolean;
  affected_count: number;
  message: string;
}

export async function performBulkAction(
  request: BulkActionRequest
): Promise<ApiResponse<BulkActionResponse>> {
  return apiClient.post<BulkActionResponse>('/lawyer/cases/bulk-action', request);
}
