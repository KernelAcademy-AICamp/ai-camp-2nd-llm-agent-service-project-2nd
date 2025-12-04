/**
 * Detective Portal Types
 * 003-role-based-ui Feature - US5
 */

// ============== Enums ==============

export type InvestigationStatus =
  | 'pending'
  | 'active'
  | 'review'
  | 'completed'
  | 'rejected';

export type RecordType = 'observation' | 'photo' | 'note' | 'video' | 'audio';

export type ScheduleEventType = 'field' | 'meeting' | 'deadline' | 'other';

export type TransactionStatus = 'pending' | 'completed' | 'cancelled';

// ============== Dashboard Types ==============

export interface DashboardStats {
  active_investigations: number;
  pending_requests: number;
  completed_this_month: number;
  monthly_earnings: number;
}

export interface InvestigationSummary {
  id: string;
  title: string;
  lawyer_name?: string;
  status: InvestigationStatus;
  deadline?: string;
  record_count: number;
}

export interface ScheduleItem {
  id: string;
  time: string;
  title: string;
  type: ScheduleEventType;
}

export interface DetectiveDashboardResponse {
  user_name: string;
  stats: DashboardStats;
  active_investigations: InvestigationSummary[];
  today_schedule: ScheduleItem[];
}

// ============== Case Types ==============

export interface CaseListItem {
  id: string;
  title: string;
  status: InvestigationStatus;
  lawyer_name?: string;
  client_name?: string;
  deadline?: string;
  record_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface DetectiveCaseListResponse {
  items: CaseListItem[];
  total: number;
}

export interface FieldRecord {
  id: string;
  record_type: RecordType;
  content: string;
  gps_lat?: number;
  gps_lng?: number;
  photo_url?: string;
  created_at: string;
}

export interface DetectiveCaseDetailResponse {
  id: string;
  title: string;
  description?: string;
  status: InvestigationStatus;
  lawyer_name?: string;
  lawyer_email?: string;
  client_name?: string;
  deadline?: string;
  records: FieldRecord[];
  created_at?: string;
  updated_at?: string;
}

// ============== Action Types ==============

export interface AcceptRejectResponse {
  success: boolean;
  message: string;
  case_id: string;
  new_status: InvestigationStatus;
}

export interface RejectRequest {
  reason: string;
}

// ============== Record Types ==============

export interface FieldRecordRequest {
  record_type: RecordType;
  content: string;
  gps_lat?: number;
  gps_lng?: number;
  photo_url?: string;
}

export interface FieldRecordResponse {
  success: boolean;
  record_id: string;
  message: string;
}

// ============== Report Types ==============

export interface ReportRequest {
  summary: string;
  findings: string;
  conclusion: string;
  attachments?: string[];
}

export interface ReportResponse {
  success: boolean;
  report_id: string;
  message: string;
  case_status: InvestigationStatus;
}

// ============== Earnings Types ==============

export interface EarningsSummary {
  total_earned: number;
  pending_payment: number;
  this_month: number;
}

export interface Transaction {
  id: string;
  case_id?: string;
  case_title?: string;
  amount: number;
  status: TransactionStatus;
  description?: string;
  created_at?: string;
}

export interface EarningsResponse {
  summary: EarningsSummary;
  transactions: Transaction[];
}
