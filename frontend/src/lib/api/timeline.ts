/**
 * Timeline API Client
 * Handles timeline data fetching for evidence timeline feature
 *
 * Feature: 002-evidence-timeline
 */

import { apiRequest, ApiResponse } from './client';
import { TimelineResult, TimelineFilter } from '@/types/timeline';

/**
 * API TimelineEvent type - matches backend snake_case convention
 */
export interface ApiTimelineEvent {
    event_id: string;
    evidence_id: string;
    case_id: string;
    timestamp: string | null;
    date: string;
    time: string;
    description: string;
    content_preview?: string;
    event_type: string;
    labels: string[];
    speaker?: string;
    source_file: string;
    significance: number;
    is_key_evidence: boolean;
    metadata?: Record<string, unknown>;
}

/**
 * API TimelineResult type - matches backend snake_case convention
 */
export interface ApiTimelineResult {
    case_id: string;
    events: ApiTimelineEvent[];
    total_count: number;
    filtered_count: number;
    has_more: boolean;
    date_range: {
        start: string | null;
        end: string | null;
    };
    events_by_type: Record<string, number>;
    events_by_label: Record<string, number>;
    key_events_count: number;
    generated_at: string;
}

/**
 * Convert snake_case API response to camelCase frontend type
 */
function mapApiTimelineResult(api: ApiTimelineResult): TimelineResult {
    return {
        caseId: api.case_id,
        events: api.events.map(e => ({
            eventId: e.event_id,
            evidenceId: e.evidence_id,
            caseId: e.case_id,
            timestamp: e.timestamp,
            date: e.date,
            time: e.time,
            description: e.description,
            contentPreview: e.content_preview,
            eventType: e.event_type as TimelineResult['events'][0]['eventType'],
            labels: e.labels,
            speaker: e.speaker,
            sourceFile: e.source_file,
            significance: e.significance,
            isKeyEvidence: e.is_key_evidence,
            metadata: e.metadata,
        })),
        totalCount: api.total_count,
        filteredCount: api.filtered_count,
        hasMore: api.has_more,
        dateRange: api.date_range,
        eventsByType: api.events_by_type,
        eventsByLabel: api.events_by_label,
        keyEventsCount: api.key_events_count,
        generatedAt: api.generated_at,
    };
}

/**
 * Build query string from filter
 */
function buildQueryString(filter?: TimelineFilter): string {
    if (!filter) return '';

    const params = new URLSearchParams();

    if (filter.dateStart) params.set('date_start', filter.dateStart);
    if (filter.dateEnd) params.set('date_end', filter.dateEnd);
    if (filter.labels?.length) params.set('labels', filter.labels.join(','));
    if (filter.speakers?.length) params.set('speakers', filter.speakers.join(','));
    if (filter.eventTypes?.length) params.set('event_types', filter.eventTypes.join(','));
    if (filter.keyOnly) params.set('key_only', 'true');
    if (filter.limit) params.set('limit', String(filter.limit));
    if (filter.offset) params.set('offset', String(filter.offset));
    if (filter.sortOrder) params.set('sort_order', filter.sortOrder);

    const queryString = params.toString();
    return queryString ? `?${queryString}` : '';
}

/**
 * Fetch timeline for a case with optional filtering
 *
 * @param caseId - Case ID
 * @param filter - Optional filter criteria
 * @returns Timeline result with events and statistics
 */
export async function getTimeline(
    caseId: string,
    filter?: TimelineFilter
): Promise<ApiResponse<TimelineResult>> {
    const queryString = buildQueryString(filter);
    const response = await apiRequest<ApiTimelineResult>(
        `/cases/${caseId}/timeline${queryString}`,
        { method: 'GET' }
    );

    if (response.data) {
        return {
            data: mapApiTimelineResult(response.data),
            status: response.status,
        };
    }

    return response as ApiResponse<TimelineResult>;
}
