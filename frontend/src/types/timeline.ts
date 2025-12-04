/**
 * Timeline Types
 * TypeScript type definitions for evidence timeline feature
 *
 * Feature: 002-evidence-timeline
 */

/**
 * Timeline event types matching backend enum
 */
export type TimelineEventType =
    | 'message'
    | 'document'
    | 'image'
    | 'audio'
    | 'video'
    | 'incident';

/**
 * Individual timeline event representing a piece of evidence
 */
export interface TimelineEvent {
    eventId: string;
    evidenceId: string;
    caseId: string;
    timestamp: string | null;
    date: string;
    time: string;
    description: string;
    contentPreview?: string;
    eventType: TimelineEventType;
    labels: string[];
    speaker?: string;
    sourceFile: string;
    significance: number;
    isKeyEvidence: boolean;
    metadata?: Record<string, unknown>;
}

/**
 * Filter criteria for timeline queries
 */
export interface TimelineFilter {
    dateStart?: string;
    dateEnd?: string;
    labels?: string[];
    speakers?: string[];
    eventTypes?: TimelineEventType[];
    keyOnly?: boolean;
    limit?: number;
    offset?: number;
    sortOrder?: 'asc' | 'desc';
}

/**
 * Date range for timeline data
 */
export interface DateRange {
    start: string | null;
    end: string | null;
}

/**
 * Timeline query result with events and statistics
 */
export interface TimelineResult {
    caseId: string;
    events: TimelineEvent[];
    totalCount: number;
    filteredCount: number;
    hasMore: boolean;
    dateRange: DateRange;
    eventsByType: Record<string, number>;
    eventsByLabel: Record<string, number>;
    keyEventsCount: number;
    generatedAt: string;
}
