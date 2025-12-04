/**
 * Client Portal Types
 * 003-role-based-ui Feature - US4
 */

// Progress Step
export interface ProgressStep {
  step: number;
  title: string;
  status: 'completed' | 'current' | 'pending';
  date?: string;
}

// Case Summary
export interface CaseSummary {
  id: string;
  title: string;
  status: string;
  progress_percent: number;
  lawyer_name?: string;
  next_action?: string;
  updated_at: string;
}

// Lawyer Info
export interface LawyerInfo {
  id: string;
  name: string;
  firm?: string;
  phone?: string;
  email: string;
}

// Recent Activity
export interface RecentActivity {
  id: string;
  title: string;
  description: string;
  activity_type: 'evidence' | 'message' | 'document' | 'status';
  timestamp: string;
  time_ago: string;
}

// Dashboard Response
export interface ClientDashboardResponse {
  user_name: string;
  case_summary?: CaseSummary;
  progress_steps: ProgressStep[];
  lawyer_info?: LawyerInfo;
  recent_activities: RecentActivity[];
  unread_messages: number;
}

// Case List Item
export interface ClientCaseListItem {
  id: string;
  title: string;
  status: string;
  progress_percent: number;
  evidence_count: number;
  lawyer_name?: string;
  created_at: string;
  updated_at: string;
}

// Case List Response
export interface ClientCaseListResponse {
  items: ClientCaseListItem[];
  total: number;
}

// Evidence Summary
export interface EvidenceSummary {
  id: string;
  file_name: string;
  file_type: 'image' | 'audio' | 'video' | 'document';
  uploaded_at: string;
  status: 'pending' | 'processed' | 'verified';
  ai_labels: string[];
}

// Case Detail Response
export interface ClientCaseDetailResponse {
  id: string;
  title: string;
  description?: string;
  status: string;
  progress_percent: number;
  progress_steps: ProgressStep[];
  lawyer_info?: LawyerInfo;
  evidence_list: EvidenceSummary[];
  evidence_count: number;
  recent_activities: RecentActivity[];
  created_at: string;
  updated_at: string;
  can_upload_evidence: boolean;
}

// Evidence Upload Request
export interface EvidenceUploadRequest {
  file_name: string;
  file_type: string;
  file_size: number;
  description?: string;
}

// Evidence Upload Response
export interface EvidenceUploadResponse {
  evidence_id: string;
  upload_url: string;
  expires_in: number;
}

// Evidence Confirm Request
export interface EvidenceConfirmRequest {
  uploaded: boolean;
}

// Evidence Confirm Response
export interface EvidenceConfirmResponse {
  success: boolean;
  message: string;
  evidence_id: string;
}
