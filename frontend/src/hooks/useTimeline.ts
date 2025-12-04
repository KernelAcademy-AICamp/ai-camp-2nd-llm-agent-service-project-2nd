/**
 * Timeline Hook
 * Manages timeline data fetching and state
 *
 * Feature: 002-evidence-timeline
 */

import { useState, useEffect, useCallback } from 'react';
import { getTimeline } from '@/lib/api/timeline';
import { TimelineResult, TimelineFilter } from '@/types/timeline';

export interface UseTimelineOptions {
    /** Initial filter settings */
    initialFilter?: TimelineFilter;
    /** Auto-fetch on mount */
    autoFetch?: boolean;
}

export interface UseTimelineReturn {
    /** Timeline data */
    data: TimelineResult | null;
    /** Loading state */
    isLoading: boolean;
    /** Error message */
    error: string | null;
    /** Current filter */
    filter: TimelineFilter;
    /** Update filter and refetch */
    setFilter: (filter: TimelineFilter) => void;
    /** Update single filter field */
    updateFilter: <K extends keyof TimelineFilter>(
        key: K,
        value: TimelineFilter[K]
    ) => void;
    /** Clear all filters */
    clearFilters: () => void;
    /** Manually refetch data */
    refetch: () => Promise<void>;
    /** Load next page */
    loadMore: () => Promise<void>;
    /** Check if more data is available */
    hasMore: boolean;
}

const DEFAULT_FILTER: TimelineFilter = {
    limit: 50,
    offset: 0,
    sortOrder: 'asc',
};

/**
 * Hook for fetching and managing timeline data
 *
 * @param caseId - Case ID to fetch timeline for
 * @param options - Hook options
 * @returns Timeline data, state, and actions
 *
 * @example
 * ```tsx
 * const { data, isLoading, error, filter, setFilter } = useTimeline(caseId);
 *
 * // Filter by labels
 * setFilter({ ...filter, labels: ['폭언'] });
 *
 * // Filter by date range
 * setFilter({ ...filter, dateStart: '2024-01-01', dateEnd: '2024-12-31' });
 * ```
 */
export function useTimeline(
    caseId: string,
    options: UseTimelineOptions = {}
): UseTimelineReturn {
    const { initialFilter, autoFetch = true } = options;

    const [data, setData] = useState<TimelineResult | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilterState] = useState<TimelineFilter>({
        ...DEFAULT_FILTER,
        ...initialFilter,
    });

    // Fetch timeline data
    const fetchTimeline = useCallback(
        async (currentFilter: TimelineFilter, append = false) => {
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
        },
        [caseId, data]
    );

    // Initial fetch
    useEffect(() => {
        if (autoFetch && caseId) {
            fetchTimeline(filter);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [caseId, autoFetch]);

    // Set filter and refetch
    const setFilter = useCallback(
        (newFilter: TimelineFilter) => {
            // Reset offset when filter changes
            const filterWithResetOffset = {
                ...newFilter,
                offset: 0,
            };
            setFilterState(filterWithResetOffset);
            fetchTimeline(filterWithResetOffset);
        },
        [fetchTimeline]
    );

    // Update single filter field
    const updateFilter = useCallback(
        <K extends keyof TimelineFilter>(key: K, value: TimelineFilter[K]) => {
            setFilter({ ...filter, [key]: value });
        },
        [filter, setFilter]
    );

    // Clear all filters
    const clearFilters = useCallback(() => {
        setFilter(DEFAULT_FILTER);
    }, [setFilter]);

    // Manual refetch
    const refetch = useCallback(async () => {
        await fetchTimeline(filter);
    }, [fetchTimeline, filter]);

    // Load more (pagination)
    const loadMore = useCallback(async () => {
        if (!data?.hasMore || isLoading) return;

        const newOffset = (filter.offset || 0) + (filter.limit || 50);
        const newFilter = { ...filter, offset: newOffset };
        setFilterState(newFilter);
        await fetchTimeline(newFilter, true);
    }, [data?.hasMore, isLoading, filter, fetchTimeline]);

    return {
        data,
        isLoading,
        error,
        filter,
        setFilter,
        updateFilter,
        clearFilters,
        refetch,
        loadMore,
        hasMore: data?.hasMore ?? false,
    };
}

export default useTimeline;
