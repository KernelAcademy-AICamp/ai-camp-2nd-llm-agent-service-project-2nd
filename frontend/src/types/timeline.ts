/**
 * Timeline TypeScript types for Evidence Timeline feature
 * Feature: 002-evidence-timeline
 */

export type TimelineEventType =
    | 'message'
    | 'document'
    | 'image'
    | 'audio'
    | 'video'
    | 'incident';

export interface TimelineEvent {
    eventId: string;
    evidenceId: string;
    caseId: string;

    // Time
    timestamp: string | null;  // ISO 8601 or null for unknown dates
    date: string;              // YYYY-MM-DD or "날짜 미상"
    time: string;              // HH:MM or ""

    // Content
    description: string;
    contentPreview?: string;

    // Classification
    eventType: TimelineEventType;
    labels: string[];
    speaker?: string;          // 원고/피고/제3자/unknown
    sourceFile: string;

    // Significance
    significance: number;      // 1-5 scale
    isKeyEvidence: boolean;    // significance >= 4

    // Metadata
    metadata?: Record<string, unknown>;
}

export interface TimelineFilter {
    dateStart?: string;        // YYYY-MM-DD
    dateEnd?: string;          // YYYY-MM-DD
    labels?: string[];
    speakers?: string[];
    eventTypes?: TimelineEventType[];
    keyOnly?: boolean;

    // Pagination
    limit?: number;            // 1-100, default 50
    offset?: number;           // default 0

    // Sort
    sortOrder?: 'asc' | 'desc'; // default 'asc' (oldest first)
}

export interface TimelineResult {
    caseId: string;
    events: TimelineEvent[];

    // Pagination
    totalCount: number;
    filteredCount: number;
    hasMore: boolean;

    // Statistics
    dateRange: {
        start: string | null;
        end: string | null;
    };
    eventsByType: Record<string, number>;
    eventsByLabel: Record<string, number>;
    keyEventsCount: number;

    // Meta
    generatedAt: string;       // ISO 8601
}

// Helper type for filter state management
export interface TimelineFilterState extends TimelineFilter {
    isFiltering: boolean;
}

// Speaker options for filter dropdown
export const SPEAKER_OPTIONS = ['원고', '피고', '제3자', 'unknown'] as const;
export type SpeakerOption = typeof SPEAKER_OPTIONS[number];

// Common Article 840 labels for filter dropdown
export const COMMON_LABELS = [
    '부정행위',
    '폭행',
    '학대',
    '유기',
    '협박',
    '위협',
    '폭언',
    '계속적_불화',
    '혼인_파탄',
    '재산_문제',
    '양육_문제',
] as const;
