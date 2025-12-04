/**
 * Calendar Types
 * 003-role-based-ui Feature - US7
 *
 * Type definitions for calendar events and related data.
 */

export type CalendarEventType = 'court' | 'meeting' | 'deadline' | 'internal' | 'other';

export interface CalendarEvent {
  id: string;
  user_id: string;
  case_id?: string;
  case_title?: string;
  title: string;
  description?: string;
  event_type: CalendarEventType;
  start_time: string;
  end_time?: string;
  location?: string;
  reminder_minutes?: number;
  color?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CalendarEventCreate {
  title: string;
  event_type: CalendarEventType;
  start_time: string;
  end_time?: string;
  description?: string;
  location?: string;
  case_id?: string;
  reminder_minutes?: number;
}

export interface CalendarEventUpdate {
  title?: string;
  event_type?: CalendarEventType;
  start_time?: string;
  end_time?: string;
  description?: string;
  location?: string;
  case_id?: string;
  reminder_minutes?: number;
}

export interface CalendarEventsResponse {
  events: CalendarEvent[];
  total: number;
}

export interface UpcomingEventsResponse {
  events: CalendarEvent[];
}

export interface RemindersResponse {
  reminders: CalendarEvent[];
}

export interface EventTypeColors {
  court: string;
  meeting: string;
  deadline: string;
  internal: string;
  other: string;
}

// Event type color mapping (matches backend)
export const EVENT_TYPE_COLORS: EventTypeColors = {
  court: '#ef4444',     // Red
  meeting: '#3b82f6',   // Blue
  deadline: '#f59e0b',  // Amber
  internal: '#8b5cf6',  // Purple
  other: '#6b7280',     // Gray
};

// Korean labels for event types
export const EVENT_TYPE_LABELS: Record<CalendarEventType, string> = {
  court: '재판',
  meeting: '상담',
  deadline: '마감',
  internal: '내부회의',
  other: '기타',
};
