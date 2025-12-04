/**
 * Custom hook for Timeline data management
 * Handles data fetching, filtering, and state management
 *
 * Feature: 002-evidence-timeline
 */

import { useState, useCallback, useEffect } from 'react';
import { TimelineResult, TimelineFilter, TimelineEvent } from '@/types/timeline';
import { getTimeline } from '@/lib/api/timeline';

interface UseTimelineOptions {
    caseId: string;
    initialFilter?: Partial<TimelineFilter>;
    autoFetch?: boolean;
}

interface UseTimelineReturn {
    data: TimelineResult | null;
    events: TimelineEvent[];
    isLoading: boolean;
    error: string | null;
    filter: TimelineFilter;
    setFilter: (filter: Partial<TimelineFilter>) => void;
    resetFilter: () => void;
    refresh: () => Promise<void>;
    loadMore: () => Promise<void>;
    hasMore: boolean;
}

const DEFAULT_FILTER: TimelineFilter = {
    limit: 50,
    offset: 0,
    sortOrder: 'asc',
};

export function useTimeline({
    caseId,
    initialFilter = {},
    autoFetch = true,
}: UseTimelineOptions): UseTimelineReturn {
    const [data, setData] = useState<TimelineResult | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilterState] = useState<TimelineFilter>({
        ...DEFAULT_FILTER,
        ...initialFilter,
    });

    const fetchTimeline = useCallback(async (
        currentFilter: TimelineFilter,
        append = false
    ) => {
        if (!caseId) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await getTimeline(caseId, currentFilter);

            if (response.error) {
                setError(response.error);
                return;
            }

            if (response.data) {
                if (append && data) {
                    // Append new events for pagination
                    setData({
                        ...response.data,
                        events: [...data.events, ...response.data.events],
                    });
                } else {
                    setData(response.data);
                }
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch timeline');
        } finally {
            setIsLoading(false);
        }
    }, [caseId, data]);

    const setFilter = useCallback((newFilter: Partial<TimelineFilter>) => {
        const updatedFilter = {
            ...filter,
            ...newFilter,
            offset: 0, // Reset offset when filter changes
        };
        setFilterState(updatedFilter);
        fetchTimeline(updatedFilter, false);
    }, [filter, fetchTimeline]);

    const resetFilter = useCallback(() => {
        const resetFilterState = { ...DEFAULT_FILTER };
        setFilterState(resetFilterState);
        fetchTimeline(resetFilterState, false);
    }, [fetchTimeline]);

    const refresh = useCallback(async () => {
        const refreshFilter = { ...filter, offset: 0 };
        setFilterState(refreshFilter);
        await fetchTimeline(refreshFilter, false);
    }, [filter, fetchTimeline]);

    const loadMore = useCallback(async () => {
        if (!data?.hasMore || isLoading) return;

        const nextFilter = {
            ...filter,
            offset: (filter.offset || 0) + (filter.limit || 50),
        };
        setFilterState(nextFilter);
        await fetchTimeline(nextFilter, true);
    }, [data?.hasMore, isLoading, filter, fetchTimeline]);

    // Auto-fetch on mount
    useEffect(() => {
        if (autoFetch && caseId) {
            fetchTimeline(filter, false);
        }
        // Only run on mount
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [caseId, autoFetch]);

    return {
        data,
        events: data?.events || [],
        isLoading,
        error,
        filter,
        setFilter,
        resetFilter,
        refresh,
        loadMore,
        hasMore: data?.hasMore || false,
    };
}
